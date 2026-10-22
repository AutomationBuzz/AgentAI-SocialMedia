"""Publish one approved JPEG feed post using Meta's official Facebook Login API."""

import argparse
import hashlib
import io
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import sys
import time
import unicodedata
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

from dotenv import dotenv_values
from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parent
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class PublishError(Exception):
    pass


class AmbiguousPublish(PublishError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PublishError("Redirects are blocked; provide a direct HTTPS URL.")


def opener():
    return build_opener(ProxyHandler({}), NoRedirect(), HTTPSHandler())


def settings():
    values = {**dotenv_values(ROOT / ".env"), **os.environ}
    names = ("IG_ACCESS_TOKEN", "IG_PAGE_ID", "IG_ACCOUNT_ID",
             "IG_EXPECTED_USERNAME", "IG_API_VERSION")
    config = {name: values.get(name, "") for name in names}
    if not all(isinstance(value, str) and value.strip() for value in config.values()):
        raise PublishError("Set all five IG_* settings in the project .env or environment.")
    for name in ("IG_PAGE_ID", "IG_ACCOUNT_ID"):
        if not re.fullmatch(r"[0-9]+", config[name]):
            raise PublishError("Page and Instagram account IDs must be numeric.")
    if not re.fullmatch(r"[A-Za-z0-9_.]{1,30}", config["IG_EXPECTED_USERNAME"]):
        raise PublishError("Expected username must be a username without @.")
    if not re.fullmatch(r"v[0-9]+\.0", config["IG_API_VERSION"]):
        raise PublishError("Use an explicit supported Graph version, such as v26.0.")
    if any(character.isspace() for character in config["IG_ACCESS_TOKEN"]):
        raise PublishError("Access token must not contain whitespace.")
    return config


def validate_caption(caption):
    if not caption.strip() or len(caption) > 2200:
        raise PublishError("Caption must contain 1-2200 characters and not be blank.")
    if any(unicodedata.category(character) == "Cc" and character not in "\n\t"
           for character in caption):
        raise PublishError("Caption contains unsupported control characters.")
    if len(re.findall(r"(?<!\w)#\w+", caption)) > 30:
        raise PublishError("Caption exceeds 30 hashtags.")
    if len(re.findall(r"(?<!\w)@[A-Za-z0-9_.]+", caption)) > 20:
        raise PublishError("Caption exceeds 20 mentions.")


def validate_url(image_url):
    try:
        parsed = urlsplit(image_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment
                or parsed.port not in (None, 443)
                or any(character.isspace() or ord(character) < 32 for character in image_url)):
            raise ValueError
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global
                                for address in addresses):
            raise ValueError
    except (ValueError, OSError):
        raise PublishError("Image URL must be direct public HTTPS without credentials, query, fragment or private IPs.") from None


def inspect_image(image_url):
    validate_url(image_url)
    try:
        request = Request(image_url, headers={"Accept": "image/jpeg"})
        with opener().open(request, timeout=30) as response:
            if response.status != 200 or response.headers.get_content_type() != "image/jpeg":
                raise PublishError("Image must return HTTP 200 and Content-Type image/jpeg without authentication.")
            content = response.read(MAX_IMAGE_BYTES + 1)
    except (OSError, URLError, ValueError):
        raise PublishError("Public JPEG download failed; no credentials were sent to the media host.") from None
    if len(content) > MAX_IMAGE_BYTES:
        raise PublishError("JPEG exceeds the conservative 8 MiB limit.")
    try:
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
            if (image.format != "JPEG" or image.mode != "RGB"
                    or not 320 <= width <= 1440 or not 0.8 <= width / height <= 1.91):
                raise PublishError("Use an RGB JPEG, width 320-1440, aspect ratio 4:5 through 1.91:1.")
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise PublishError("JPEG is invalid or cannot be safely decoded.") from None
    return {"width": width, "height": height,
            "sha256": hashlib.sha256(content).hexdigest()}


class Graph:
    def __init__(self, config):
        self.base = "https://graph.facebook.com/" + config["IG_API_VERSION"]
        self.token = config["IG_ACCESS_TOKEN"]

    def call(self, method, path, **parameters):
        encoded = urlencode(parameters).encode("utf-8")
        url = self.base + "/" + path
        data = encoded if method == "POST" else None
        if method == "GET" and parameters:
            url += "?" + encoded.decode("utf-8")
        request = Request(url, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        try:
            with opener().open(request, timeout=30) as response:
                payload = json.loads(response.read(1024 * 1024))
                if response.status != 200 or not isinstance(payload, dict) or "error" in payload:
                    raise PublishError("Meta rejected the request; check permissions and platform eligibility.")
                return payload
        except HTTPError as error:
            raise PublishError("Meta returned HTTP %s; check permissions, quota and platform requirements." % error.code) from None
        except (OSError, URLError, ValueError):
            raise PublishError("Meta transport or response failed; no automatic retry was made.") from None


def verify_identity(graph, config):
    page_id = config["IG_PAGE_ID"]
    account_id = config["IG_ACCOUNT_ID"]
    page = graph.call("GET", page_id, fields="id,instagram_business_account")
    linked = page.get("instagram_business_account")
    if (page.get("id") != page_id or not isinstance(linked, dict)
            or linked.get("id") != account_id):
        raise PublishError("Page is not linked to the expected Instagram account. Publishing blocked.")
    identity = graph.call("GET", account_id, fields="id,username")
    if (identity.get("id") != account_id
            or identity.get("username", "").lower() != config["IG_EXPECTED_USERNAME"].lower()):
        raise PublishError("Official identity does not match the expected professional account.")
    return {"id": account_id, "username": identity["username"]}


def check_quota(graph, account_id):
    result = graph.call("GET", account_id + "/content_publishing_limit", fields="quota_usage,config")
    try:
        entry = result["data"][0]
        usage = entry["quota_usage"]
        total = entry["config"]["quota_total"]
        if not isinstance(usage, int) or not isinstance(total, int) or not 0 <= usage < total:
            raise ValueError
    except (KeyError, IndexError, TypeError, ValueError):
        raise PublishError("Publishing quota is exhausted or could not be verified.") from None


def numeric_id(payload):
    identifier = payload.get("id")
    if not isinstance(identifier, str) or not re.fullmatch(r"[0-9]+", identifier):
        raise PublishError("Meta response did not include a valid ID.")
    return identifier


def publish(graph, account_id, caption, image_url, attempt_path):
    container_id = numeric_id(graph.call("POST", account_id + "/media",
                                         image_url=image_url, caption=caption))
    print("Container ID:", container_id)
    for attempt in range(5):
        state = graph.call("GET", container_id, fields="status_code").get("status_code")
        if state == "FINISHED":
            break
        if state != "IN_PROGRESS" or attempt == 4:
            raise PublishError("Container is not ready; no publish call was sent.")
        time.sleep(60)
    attempt_path.parent.mkdir(mode=0o700, exist_ok=True)
    try:
        with attempt_path.open("x", encoding="utf-8") as handle:
            json.dump({"container_id": container_id, "account_id": account_id}, handle)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        raise PublishError("A publish attempt exists for this content. Review manually; do not retry.") from None
    try:
        return numeric_id(graph.call("POST", account_id + "/media_publish", creation_id=container_id)), container_id
    except Exception:
        raise AmbiguousPublish(
            "Publish outcome is unconfirmed. STOP: do not rerun or retry. "
            "Inspect the account and container through Meta's official tools. "
            "The attempt guard remains; no success receipt was written."
        ) from None


def run(args, config, graph):
    caption = args.caption_file.read_text(encoding="utf-8")
    validate_caption(caption)
    token = config["IG_ACCESS_TOKEN"]
    if any(token in value for value in (caption, args.image_url, config["IG_EXPECTED_USERNAME"])):
        raise PublishError("A public input contains the access token; refusing to display or publish it.")
    image = inspect_image(args.image_url)
    identity = verify_identity(graph, config)
    check_quota(graph, identity["id"])
    digest = hashlib.sha256((identity["id"] + "\0" + image["sha256"] + "\0" + caption).encode()).hexdigest()
    attempt_path = ROOT / ".attempts" / (digest + ".json")
    receipt_path = ROOT / "receipts" / (digest + ".json")
    print("Verified Instagram: @%s (ID %s)" % (identity["username"], identity["id"]))
    print("JPEG: %s x %s; SHA-256 %s" % (image["width"], image["height"], image["sha256"]))
    print("Public image:", args.image_url)
    print("Caption preview:\n" + caption)
    print("The 10-minute target is best-effort: credentials, hosting and Meta availability determine timing.")
    if not args.publish:
        print("DRY RUN: read-only checks complete; no containers, publish calls or files written.")
        return
    if attempt_path.exists() or receipt_path.exists():
        raise PublishError("This content has an existing attempt or receipt. Manual review required; no retry.")
    if not args.confirm_publish:
        try:
            confirmation = input("Type PUBLISH to authorize this exact feed post once: ")
        except EOFError:
            raise PublishError("No confirmation received; nothing was published.") from None
        if confirmation != "PUBLISH":
            raise PublishError("Cancelled; nothing was published.")
    media_id, container_id = publish(graph, identity["id"], caption, args.image_url, attempt_path)
    print("CONFIRMED SUCCESS. Instagram media ID:", media_id)
    receipt = {
        "status": "published", "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "account_id": identity["id"], "username": identity["username"],
        "media_id": media_id, "container_id": container_id,
        "image_sha256": image["sha256"],
        "caption_sha256": hashlib.sha256(caption.encode()).hexdigest(),
        "graph_api_version": config["IG_API_VERSION"],
    }
    try:
        receipt_path.parent.mkdir(mode=0o700, exist_ok=True)
        with receipt_path.open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2)
            handle.write("\n")
    except OSError:
        raise PublishError("Publishing SUCCEEDED (media ID %s), but receipt persistence failed. Do not republish." % media_id) from None
    print("Non-secret success receipt:", receipt_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-url", required=True, help="Direct public HTTPS RGB JPEG; no signed query URLs")
    parser.add_argument("--caption-file", required=True, type=Path, help="UTF-8 file with the approved caption")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Default: validate and preview without writes")
    mode.add_argument("--publish", action="store_true", help="Publish after exactly one confirmation")
    parser.add_argument("--confirm-publish", action="store_true",
                        help="The one confirmation when this exact post has already been explicitly authorized")
    args = parser.parse_args()
    if args.confirm_publish and not args.publish:
        parser.error("--confirm-publish requires --publish")
    try:
        config = settings()
        run(args, config, Graph(config))
    except KeyboardInterrupt:
        print("Stopped. If a publish attempt was sent, treat its outcome as unknown and do not retry.", file=sys.stderr)
        return 2
    except PublishError as error:
        print(str(error), file=sys.stderr)
        return 2
    except Exception:
        print("Operation stopped; details suppressed to protect credentials. Review any attempt guard before rerunning.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())