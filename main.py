from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import execjs

app = FastAPI()

@app.get("/")
async def redirect_to_github():
    return RedirectResponse(url="https://github.com/S4tyendra/railway-api/tree/main#warning")

@app.get("/pnr/{pnr_number}", response_class=HTMLResponse)
async def get_pnr(pnr_number: int, is_json: bool = True):
    url = f"https://www.confirmtkt.com/pnr-status/{pnr_number}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=100)
        resp.raise_for_status()
        html = resp.text

        da = BeautifulSoup(html, 'html.parser').find_all("script")[13].text

        js_code = da.split("if (data === null)", 1)[0].replace("$", "")
        data = execjs.compile(js_code).eval("data")

        del data['ShowBlaBlaAd']
        del data['ShowCab']
        del data['Ads']
        del data['WebsiteEvents']
        del data['PnrAlternativeAdPosition']
        del data['WebsiteAds']

        if is_json:
            return JSONResponse(data)
        else:
            text_result = ""
            for key, value in data.items():
                if not isinstance(value, list):
                    text_result += f"<b>{key}</b>: {value}<br>"
                else:
                    for dat in value:
                        text_result += f"<strong>Passenger {dat.get('Number')}</strong><br>"
                        del dat['Number']
                        for dat_key, dat_value in dat.items():
                            text_result += f"&nbsp;&nbsp;{dat_key}: {dat_value}<br>"

            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>PNR Status</title>
                <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #343a40; /* Dark background color */
                        color: #ffffff; /* Light text color */
                        padding: 20px;
                    }}
                    .pnr-data {{
                        background-color: #343a40; /* Dark card background color */
                        color: #ffffff; /* Light text color */
                        border-radius: 5px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="row">
                        <div class="col-12">
                            <div class="pnr-data">
                                <!-- Formatted text data goes here -->
                                {text_result}
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            return HTMLResponse(content=html_template)
    except requests.exceptions.RequestException as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
