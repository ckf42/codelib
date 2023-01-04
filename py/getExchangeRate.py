import requests as rq
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('amount',
                    type=float,
                    nargs='?',
                    default=1.0,
                    help="The amount of original currency. Defaults to 1.0")
parser.add_argument('fromCurr',
                    type=str,
                    help="The currency to exchange from")
parser.add_argument('toCurr',
                    type=str,
                    help="The currency to exchange to")
parser.add_argument('--thousand',
                    action='store_true',
                    help="Use thousand separator (3-digit) instead of "
                    "the default myriad separator (4-digit)")
parser.add_argument('--decimal',
                    type=int,
                    default=2,
                    help="The number of decimal places to keep. "
                    "Defaults to 2")
parser.add_argument('--backend',
                    type=str,
                    choices=['currency-api', 'ecb'],
                    default='ecb',
                    help="The backend API to query. "
                    "Currently support currency-api and ecb (European Central Bank). "
                    "Affects what currencies are supported. "
                    "For ECB, the rate is computed with EUR as exchange medium "
                    "and may be inaccurate if neither currency is EUR. "
                    "Defaults to ecb")
args = parser.parse_args()


def formatAmount(amount: float,
                 decimalPlaces: int = args.decimal,
                 separatePlaces: int = 3 if args.thousand else 4) -> str:
    assert decimalPlaces >= 0, "Negative decimal places"
    isNeg = amount < 0
    amount = abs(amount)
    integerPart = str(int(amount))[::-1]
    decimalPart = amount - int(amount)
    sepParts = tuple(integerPart[idx:min(len(integerPart), idx + separatePlaces)]
                     for idx in range(0, len(integerPart), separatePlaces))
    outputRes = [','.join(p[::-1] for p in sepParts[::-1])]
    if decimalPart != 0:
        outputRes.append('.' + str(round(decimalPart, decimalPlaces))[2:])
    if isNeg:
        outputRes.insert(0, '-')
    return ''.join(outputRes)


def ecbQuery(fromCurr: str, toCurr: str) -> dict:
    # https://sdw-wsrest.ecb.europa.eu/help/
    def _ecbQueryBase(targetCurr: str) -> dict:
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

def currApiQuery(fromCurr: str, toCurr: str) -> dict:
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
}[args.backend](args.fromCurr, args.toCurr)
print(f"{formatAmount(resDict['rate'] * args.amount)} (on {resDict['time']})")

