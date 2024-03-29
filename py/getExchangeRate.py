import argparse
import datetime
import requests as rq
from random import sample

def getArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
            epilog="Notes on backends: "
            "European Central Bank (ecb) (seemingly) only has API to convert from EUR. "
            "Non-EUR conversion is done by converting to EUR first, "
            "and the result may be inaccuracy. "
            "Exchange-api (https://github.com/fawazahmed0/exchange-api, formerly Currency-api) "
            "also has exchange rates for cryptocurrencies. "
            "Exchange Rate API (https://www.exchangerate-api.com) "
            "is queried via their open access endpoint, "
            "which has a 20-minute IP-based rate limit. "
            "For supported currency code, "
            "please check the documentation for the backends. "
            "Props to the maintainers of these backends for providing these resources.")
    parser.add_argument(
            'amount',
            type=float,
            nargs='?',
            default=1.0,
            help="The amount of original currency. Defaults to 1.0")
    parser.add_argument(
            'fromCurr',
            type=str,
            help="The code for the original currency")
    parser.add_argument(
            'toCurr',
            type=str,
            help="The code for the target currency")
    parser.add_argument(
            '--thousand', '-t',
            action='store_true',
            help="Use thousand separator (3-digit, i.e. 10,000) instead of "
            "the default myriad separator (4-digit, i.e. 1,0000)")
    parser.add_argument(
            '--decimal', '-d',
           type=int,
           default=2,
           help="The number of decimal places to keep. "
           "Defaults to 2")
    backendGp = parser.add_mutually_exclusive_group()
    backendGp.add_argument(
            '--backend', '-b',
            type=str,
            choices=('ecb', 'curr-api', 'er-api'),
            default='ecb',
            help="The backend API to query. "
            "Affects what currencies are supported. "
            "Currently support ecb (European Central Bank), "
            "curr-api (exchange-api, formerly currency-api), "
            "and er-api (Exchange Rate API). "
            "Defaults to ecb")
    backendGp.add_argument(
            '--tryAll', '-a',
            action='store_true',
            help="Try all backends and report the first one that responses")
    parser.add_argument(
            '--random', '-r',
            action='store_true',
            help="Try all backends in random order. "
            "Ignored if presents without --tryAll")
    args = parser.parse_args()
    if args.random and not args.tryAll:
        parser.error("Cannot specify --random without --tryAll")
    return args


def formatAmount(amount: float, args: argparse.Namespace) -> str:
    assert args.decimal >= 0, "Negative decimal places"
    separatePlaces = 3 if args.thousand else 4
    isNeg = amount < 0
    amount = abs(amount)
    integerPart = str(int(amount))[::-1]
    decimalPart = amount - int(amount)
    sepParts = tuple(integerPart[idx:min(len(integerPart), idx + separatePlaces)]
                     for idx in range(0, len(integerPart), separatePlaces))
    outputRes = [','.join(p[::-1] for p in sepParts[::-1])]
    if decimalPart != 0:
        outputRes.append('.' + str(round(decimalPart, args.decimal))[2:])
    if isNeg:
        outputRes.insert(0, '-')
    return ''.join(outputRes)


def ecbQuery(fromCurr: str, toCurr: str) -> dict:
    # https://data-api.ecb.europa.eu/help/
    def _ecbQueryBase(targetCurr: str) -> dict:
        # only seems to have api to convert from eur
        ecbAddr = f'https://data-api.ecb.europa.eu/service/data/EXR/D.{targetCurr.upper()}.EUR.SP00.A'
        reqPara = {
            'startPeriod': (
                datetime.date.today() - datetime.timedelta(days=14)
                ).isoformat(),
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
            except rq.exceptions.JSONDecodeError as e:
                if resp.headers['Content-Length'] == '0':
                    raise RuntimeError({
                        'msg': f"Empty response. Currency may not be supported: {targetCurr}"
                    }) from e
                else:
                    raise RuntimeError({'msg': "Failed parsing response",
                                        'respContent': resp.content}) from e
        elif resp.status_code == 404:
            raise RuntimeError({'msg': f"Currency not supported: {targetCurr}"})
        else:
            raise RuntimeError({'msg': f"Request returned with {resp.status_code}"})
    todayDate = datetime.date.today().isoformat()
    exch1 = _ecbQueryBase(fromCurr) \
            if fromCurr.upper() != 'EUR' \
            else {'rate': 1, 'time': todayDate}
    exch2 = _ecbQueryBase(toCurr) \
            if toCurr.upper() != 'EUR' \
            else {'rate': 1, 'time': todayDate}
    return {'rate': exch2['rate'] / exch1['rate'],
            'time': min(exch1['time'], exch2['time'])}

def currApiQuery(fromCurr: str, toCurr: str) -> dict:
    # thanks exchange-api (https://github.com/fawazahmed0/exchange-api)
    # formerly currency-api (https://github.com/fawazahmed0/currency-api) 
    # for open access without needing a key
    # apiAddr = f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{fromCurr.lower()}/{toCurr.lower()}.min.json'
    apiAddr = f'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{fromCurr.lower()}.min.json'
    # TODO: how to check when fallback is needed?
    # fallback_apiAddr = f'https://latest.currency-api.pages.dev/v1/currencies/{fromCurr.lower()}.min.json'
    resp = rq.get(apiAddr)
    if resp.status_code == 403:
        raise RuntimeError({'msg': f"Currency may not be supported: {fromCurr.lower()}"})
    try:
        respJs = resp.json()
        return {'time': respJs['date'], 'rate': respJs[fromCurr.lower()][toCurr.lower()]}
    except rq.exceptions.JSONDecodeError as e:
        raise RuntimeError({'msg': "Failed parsing response",
                            'respContent': resp.content}) from e
    except KeyError as e:
        raise RuntimeError({'msg': f"No record from {fromCurr.lower()} to {toCurr.lower()}"}) \
            from e

def erApiQuery(fromCurr: str, toCurr: str) -> dict:
    # thanks https://www.exchangerate-api.com for providing open access endpoint
    # for doc, see https://www.exchangerate-api.com/docs/free
    apiAddr = f'https://open.er-api.com/v6/latest/{fromCurr}'
    resp = rq.get(apiAddr)
    if resp.status_code == 429:
        raise RuntimeError({
            'msg': 'Rate limited by Exchange Rate API. Please wait for about 20 minutes'
            })
    try:
        respJs = resp.json()
        if respJs['result'] != 'success':
            raise RuntimeError({
                'msg': f"Request faild due to error: {respJs['error-type']}"
                })
        elif toCurr.upper() not in respJs['rates']:
            raise RuntimeError({
                'msg': f"Has not data to convert from {fromCurr} to {toCurr}"
                })
        else:
            return {
                'time': str(datetime.date.fromtimestamp(respJs['time_last_update_unix'])),
                'rate': respJs['rates'][toCurr.upper()]
            }
    except rq.exceptions.JSONDecodeError as e:
        raise RuntimeError({'msg': "Failed parsing response",
                            'respContent': resp.Content}) from e


def main():
    args = getArgs()
    backendDict = {
        'ecb': ecbQuery,
        'curr-api': currApiQuery,
        'er-api': erApiQuery,
    }
    if args.tryAll:
        querySucceed = False
        for backend in (sample(tuple(backendDict.keys()), k=len(backendDict))
                        if args.random else backendDict):
            print(f"Querying backend {backend}")
            try:
                resDict = backendDict[backend](args.fromCurr, args.toCurr)
                print(f"{formatAmount(resDict['rate'] * args.amount, args)} (on {resDict['time']})")
                querySucceed = True
                break
            except RuntimeError as e:
                # silent gracefully
                print(f"Query fail: {e.args[0]['msg']}")
                if 'respContent' in e.args[0]:
                    print(f"Received content: {e.args[0]['respContent']}")
        if not querySucceed:
            raise RuntimeError("All backend failed")
    else:
        resDict = backendDict[args.backend](args.fromCurr, args.toCurr)
        print(f"{formatAmount(resDict['rate'] * args.amount, args)} (on {resDict['time']})")

if __name__ == '__main__':
    main()

