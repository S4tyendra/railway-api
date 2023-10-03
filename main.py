from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse
import requests
from bs4 import BeautifulSoup
import execjs
import json

app = FastAPI()

@app.get("/")
async def redirect_to_github():
    return RedirectResponse(url="https://github.com/S4tyendra/railway-api/tree/main#warning")

@app.get("/pnr/{pnr_number}")
async def get_pnr(pnr_number: str, is_json: bool = True):
    url = f"https://www.confirmtkt.com/pnr-status/{pnr_number}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

        da = BeautifulSoup(html, 'html.parser').find_all("script")[13].text

        js_code = da.split("if (data === null)", 1)[0].replace("$", "")
        data = execjs.compile(js_code).eval("data")

        del data['ShowBlaBlaAd']
        del data['ShowCab']
        del data['Ads']
        del data['WebsiteEvents']

        if is_json:
            return data
        else:
            text_result = ""
            for key, value in data.items():
                if type(value) != list:
                    text_result += f"{key} : {value}\n"
                else:
                    for dat in value:
                        text_result += f"  Passenger {dat.get('Number')}\n"
                        del dat['Number']
                        for dat_key, dat_value in dat.items():
                            text_result += f"    {dat_key} : {dat_value}\n"
            return text_result
    except requests.exceptions.RequestException as e:
        # Handle any request exceptions (e.g., network issues)
        return {"error": "An error occurred while fetching PNR status. Please try again later."}

# Example usage:
# Access the PNR status data in JSON format: /pnr/6852918353
# Access the PNR status data in text format: /pnr/6852918353?is_json=false
