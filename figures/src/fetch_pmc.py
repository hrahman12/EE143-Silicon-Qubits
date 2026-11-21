"""Download figure images + licence JSON for CC BY papers from the PMC Open Access S3 bucket.
Usage: python3 figures/src/fetch_pmc.py   (writes into figures/raw/<key>/)"""
import re, json, os, subprocess, urllib.request
PAPERS = {  # key: PMCID  (licences checked in Europe PMC + article XML)
 "Stock2024":"PMC11475292", "Constantinou2024":"PMC10808421", "Constantinou2023":"PMC10520640",
 "Tseng2023":"PMC10115406", "Hofmann2023":"PMC10108107", "Lundgren2023":"PMC10461293",
 "Stock2020":"PMC7146850", "Thorvaldson2025":"PMC12014505", "Edlbauer2025":"PMC12711558",
 "Wang2022":"PMC9652469",
}
B="https://pmc-oa-opendata.s3.amazonaws.com"
def get(u):
    return subprocess.run(["curl","-s","--max-time","60",u],capture_output=True).stdout
for key,pmc in PAPERS.items():
    out=f"figures/raw/{key}"; os.makedirs(out,exist_ok=True)
    lst=get(f"{B}/?list-type=2&prefix={pmc}").decode()
    keys=re.findall(r"<Key>([^<]+)</Key>",lst)
    for k in keys:
        fn=os.path.join(out,os.path.basename(k))
        if k.endswith(".pdf"): continue
        if not os.path.exists(fn):
            open(fn,"wb").write(get(f"{B}/{k}"))
    print(key,pmc,[os.path.basename(k) for k in keys])
