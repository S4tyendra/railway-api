from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import json 
from datetime import datetime
import logging

logging.basicConfig(filename="app.log", level=logging.DEBUG)

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Received request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response: {response.status_code}")
    return response

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

        data = json.loads(''.join([c for i, c in enumerate((da.split("if (data === null)", 1)[0].split("data =")[-1]).strip()) if i < len((da.split("if (data === null)", 1)[0].split("data =")[-1].strip())) - 1]))
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



def live_status(train,date):

        url = f"https://www.confirmtkt.com/train-running-status/{train}?Date={date}"
        headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Dnt": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.1234.0 Safari/537.36"
}

        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text
        soup1 = BeautifulSoup(html, 'html.parser').find_all("script", {"type": "text/javascript"})[2].text
        update_message = BeautifulSoup(html,'html.parser').find_all("div",{"class":"train-update__status"})[0].text.strip()
        # print(update_message)
        csc = str(soup1.split('currentStnCode = "')[1].split('";')[0])
        css = str(soup1.split('currentStnName = "')[1].split('";')[0])
        da = json.loads(soup1.split("var data = ",1)[1].split("if (data)")[0].strip()[:-1])
        src = f"{da['SourceCode']} - {da['Source']}"
        dest = f"{da['DestinationCode']} - {da['Destination']}"
        schedule = da['Schedule']
        return {
            'message':update_message,
            'CurrentS':csc,
            'CurrentSName': css,
            'src': src,
            'dest':dest,
            'schedule':schedule

        }

@app.get("/train-status")
async def get_train_status(train: str, date: str):
    try:
        train_status = live_status(train, date)
        return train_status
    except Exception as e:
        return {"error": str(e)}
    
    
@app.get("/logs", response_class=HTMLResponse)
async def get_logs():
    try:
        with open("app.log", "r") as file:
            logs = file.read()
        return HTMLResponse(content=f"<pre>{logs}</pre>")
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)