import requests as rq
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('amount',
                    type=float,
                    nargs='?',
                    default=1,
                    help="The amount of original currency. Defaults to 1")
parser.add_argument('initCurr',
                    type=str,
                    help="The currency to exchange from")
parser.add_argument('destCurr',
                    type=str,
                    help="The currency to exchange to")
parser.add_argument('--backend',
                    type=str,
                    choices=['currency-api', 'ecb'],
                    default='currency-api',
                    help="The backend API to query. Defaults to currency-api")
args = parser.parse_args()

def ecbQuery(fromCurr, toCurr):
    # https://sdw-wsrest.ecb.europa.eu/help/
    def _ecbQueryBase(targetCurr):
        ecbAddr = f'https://sdw-wsrest.ecb.europa.eu/service/data/EXR/D.{targetCurr.upper()}.EUR.SP00.A'
        reqPara = {
            'startPeriod': (datetime.date.today() - datetime.timedelta(days=14)).isoformat(),
            'format': 'jsondata',
            'detail': 'dataonly',
            'lastNObservations': '1',
        }
        resp = rq.get(ecbAddr, params=reqPara)
        if resp.status_code == 200:
            try:
                respJs = resp.json()
                respTime = respJs['structure']['dimensions']['observation'][0]['values'][0]['id']
                respVal = respJs['dataSets'][0]['series']['0:0:0:0:0']['observations']['0'][0]
                return {'rate': respVal, 'time': respTime}
            except:
                raise RuntimeError("Failed parsing response")
        else:
            raise RuntimeError(f"Request returned with {resp.status_code}")
    exch1 = _ecbQueryBase(fromCurr) if fromCurr.upper() != 'EUR' else {'rate': 1, 'time': datetime.date.today().isoformat()}
    exch2 = _ecbQueryBase(toCurr) if toCurr.upper() != 'EUR' else {'rate': 1, 'time': datetime.date.today().isoformat()}
    return {'rate': exch2['rate'] / exch1['rate'], 'time': min(exch1['time'], exch2['time'])}

def currApiQuery(fromCurr, toCurr):
    # https://github.com/fawazahmed0/currency-api
    apiAddr = f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{fromCurr.lower()}/{toCurr.lower()}.min.json'
    resp = rq.get(apiAddr)
    try:
        respJs = resp.json()
        return {'time': respJs['date'], 'rate': respJs[toCurr.lower()]}
    except:
        raise RuntimeError("Failed parsing response")

resDict = {
    'ecb': ecbQuery,
    'currency-api': currApiQuery,
}[args.backend](args.initCurr, args.destCurr)
print(f"{round(resDict['rate'] * args.amount, 6)} (on {resDict['time']})")

