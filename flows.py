import sys
from collections import defaultdict
from scapy.all import rdpcap, IP, TCP, UDP


def flow_key(pkt):
    """Return a direction-independent key identifying which conversation
    this packet belongs to."""
    ip = pkt[IP]
    if TCP in pkt:
        proto, sport, dport = "TCP", pkt[TCP].sport, pkt[TCP].dport
    elif UDP in pkt:
        proto, sport, dport = "UDP", pkt[UDP].sport, pkt[UDP].dport
    else:
        return None
    a = (ip.src, sport)
    b = (ip.dst, dport)
    left, right = sorted([a, b])
    return (left[0], left[1], right[0], right[1], proto)


packets = rdpcap(sys.argv[1])
label = sys.argv[2] if len(sys.argv) > 2 else "unknown"
print(f"Loaded {len(packets)} packets\n")

flows = defaultdict(list)
for pkt in packets:
    if IP not in pkt:
        continue
    key = flow_key(pkt)
    if key:
        flows[key].append(pkt)

print(f"Grouped into {len(flows)} flows\n")

rows = []
for key, pkts in flows.items():
    src_ip, src_port, dst_ip, dst_port, proto = key
    duration = float(pkts[-1].time - pkts[0].time)
    total_bytes = sum(len(p) for p in pkts)
    syn_count = sum(1 for p in pkts if TCP in p and p[TCP].flags.S and not p[TCP].flags.A)
    rows.append({
        "endpoints": f"{src_ip}:{src_port} <-> {dst_ip}:{dst_port}",
        "proto": proto,
        "packets": len(pkts),
        "bytes": total_bytes,
        "duration": duration,
        "syns": syn_count,
        "label": label,
    })

rows.sort(key=lambda r: r["packets"], reverse=True)

print(f"{'ENDPOINTS':<40}{'PROTO':<6}{'PKTS':>5}{'BYTES':>8}{'DUR(s)':>8}{'SYN':>4}")
print("-" * 78)
for r in rows:
    print(f"{r['endpoints']:<40}{r['proto']:<6}{r['packets']:>5}"
          f"{r['bytes']:>8}{r['duration']:>8.2f}{r['syns']:>4}")

import csv

with open("flows.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["endpoints", "proto", "packets", "bytes", "duration", "syns", "label"])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"\nSaved {len(rows)} flows to flows.csv")
