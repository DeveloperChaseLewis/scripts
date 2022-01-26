import bs4
import json
import parse
import argparse
import requests
import pandas as pd
import alive_progress as ap
from os import path

def get_mod_gitlinks(path: str):
    links = []
    with open(path) as f:
        for line in f.readlines(): 
            matches = parse.findall("{:s}github.com/{}{:s}v{:d}.{:d}.{:d}",line)
            for result in matches:
                links.append((0,f"github.com/{result.fixed[1]}"))

    return links

def get_npm_links(path: str):
    links = []
    with open(path) as f:
        packageJson = json.load(f)
        if "dependencies" not in packageJson:
            print("No `dependencies` field found in package json")
            exit()

        dependencies = packageJson["dependencies"]
        for d in dependencies:
            links.append((1,f"npmjs.com/package/{d}"))

    return links


    return links
    return []

def get_license_from_github(link: str):
        try:
            licenseType = "Unknown"
            html = requests.get(f"https://{link}")
            soup = bs4.BeautifulSoup(html.text,'html.parser')
            license = soup.select('h3:-soup-contains("License") + div.mt-2 > a')
            if len(license) > 0:
                licenseType = license[0].get_text()
                if "View" in licenseType:
                    licenseType = "Unknown"

            return licenseType.strip('"').strip()
        except Exception as err:
            print(err)
            return "Error"

def get_license_from_npm(link: str):
        try:
            licenseType = "Unknown"
            html = requests.get(f"https://{link}")
            soup = bs4.BeautifulSoup(html.text,'html.parser')
            license = soup.select('h3:-soup-contains("License") + p')
            if len(license) > 0:
                licenseType = license[0].get_text()
            return licenseType.strip('"').strip()
        except Exception as err:
            print(err)
            return "Error"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape config files for license info')
    parser.add_argument('--file',dest='file',type=str,help='file to be parsed')
    parser.add_argument('--repo',dest='repo',type=str,help='repo that should be added to the sheet',default="")
    parser.add_argument('--lang',dest='lang',type=str,help='programming language constant',default="Go")
    parser.add_argument('--side',dest='side',type=str,help='ServerSide or Distributed',default='Server-Side')
    parser.add_argument('--output',dest='output',type=str,help='output csv file',default="./o.csv")
    parser.add_argument('--used',dest='used',type=str,help='source or binary inclusion',default='Binary')
    parser.add_argument('--link',dest='link',type=str,help='how is the package linked into program',default='Static')
    args = parser.parse_args()

    if not path.isfile(args.file):
        print(f"'{args.file}' does not exist")
        exit()

    links = []
    if args.file.endswith(".mod"):
        links = get_mod_gitlinks(args.file)
    elif args.file.endswith(".json"):
        links = get_npm_links(args.file)
    else:
        print("Unsupported file type")
        exit()
    df = pd.DataFrame(columns=['repo','Package Name','Used as source or binary','License type','Server-Side or Distributed','Modified','Link Type','Program Lang.'])
    
    with ap.alive_bar(len(links)) as bar:
        for link in links:
            row = [
                        args.repo,
                        link[1],
                        args.used,
                        "Unknown",
                        args.side,
                        "No",
                        args.link,
                        args.lang
            ]

            licenseType = "Unknown"
            if link[0] == 0:
                licenseType = get_license_from_github(link[1])
            elif link[0] == 1:
                licenseType = get_license_from_npm(link[1])

            row[3] = licenseType
            df.loc[len(df.index)] = row
            bar()
    
        print(f"Saving output file @ {args.output}")
        df.to_csv(args.output,encoding='utf-8',index=False)
    
