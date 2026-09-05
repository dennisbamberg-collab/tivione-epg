import csv
import gzip
import io
import urllib.request
import xml.etree.ElementTree as ET

MAPPING_FILE = "tivione_epgshare_v4_mapping.csv"
OUTPUT_FILE = "tivione_epg.xml.gz"

SOURCES = [
    "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz",
]


def load_needed_ids():
    ids = set()

    with open(MAPPING_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            epg_id = (row.get("epgshare_id") or "").strip()
            if epg_id:
                ids.add(epg_id)

    return ids


def download_xml(url):
    print(f"Download: {url}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        compressed = response.read()

    return gzip.decompress(compressed)


def main():
    needed_ids = load_needed_ids()
    print(f"Benötigte EPG-IDs: {len(needed_ids)}")

    output_root = ET.Element("tv", {
        "generator-info-name": "Tivione EPGshare Builder"
    })

    channels = {}
    programmes = []

    for url in SOURCES:
        xml_data = download_xml(url)
        root = ET.fromstring(xml_data)

        for channel in root.findall("channel"):
            channel_id = channel.get("id")

            if channel_id in needed_ids:
                if channel_id not in channels:
                    channels[channel_id] = channel

        for programme in root.findall("programme"):
            channel_id = programme.get("channel")

            if channel_id in needed_ids:
                programmes.append(programme)

    print(f"Gefundene Channels: {len(channels)}")
    print(f"Gefundene Programme: {len(programmes)}")

    for channel_id in sorted(channels):
        output_root.append(channels[channel_id])

    for programme in programmes:
        output_root.append(programme)

    xml_buffer = io.BytesIO()

    ET.ElementTree(output_root).write(
        xml_buffer,
        encoding="utf-8",
        xml_declaration=True
    )

    with gzip.open(OUTPUT_FILE, "wb", compresslevel=9) as gz:
        gz.write(xml_buffer.getvalue())

    print(f"Erstellt: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
