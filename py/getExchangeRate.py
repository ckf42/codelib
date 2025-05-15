import argparse
import ast
import datetime
import operator as op
import typing as tp
from random import sample

import requests as rq

Allowed_operators: dict[tp.Type, tp.Callable] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
    ast.Pow: op.pow,
}


def stringEval(expr: str, useSuffix: bool = False) -> float:
    # WARNING: potentially unsafe
    # see https://stackoverflow.com/a/9558001
    def evaluator(node) -> float:
        match node:
            case ast.Constant(value) if isinstance(value, (int, float)):
                return value
            case ast.UnaryOp(op, operand) if type(op) in Allowed_operators:
                return Allowed_operators[type(op)](evaluator(operand))
            case ast.BinOp(left, op, right) if type(op) in Allowed_operators:
                return Allowed_operators[type(op)](evaluator(left), evaluator(right))
            case _:
                raise TypeError(f"Unsupported operation {type(node)}")
    if useSuffix:
        expr = expr.lower()
        for sym, p in (('k', 3), ('m', 6), ('b', 9)):
            expr = expr.replace(sym, f'*1e{p}')
    return evaluator(ast.parse(expr, mode='eval').body)


def getArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        epilog="Notes on backends: "
        "European Central Bank (ecb) (seemingly) only has API to convert from EUR. "
        "Non-EUR conversion is done by converting to EUR first, "
        "and the result is expected to be inaccurate. "
        "Exchange-api (https://github.com/fawazahmed0/exchange-api, "
        "formerly Currency-api) also has exchange rates for cryptocurrencies. "
        "Exchange Rate API (https://www.exchangerate-api.com) "
        "is queried via their open access endpoint, "
        "which has a 20-minute IP-based rate limit. "
        "For supported currency code, "
        "please check the documentation for the backends. "
        "Thanks to the maintainers of these backends for providing these resources.")
    parser.add_argument(
        'amount',
        type=str,
        nargs='?',
        default='1.0',
        help="The amount of original currency. "
        "A float number or a simple arithmetic expression. "
        "Support for allowed arithmetic operations is limited. "
        "Note that evaluation of such expression is ***UNSAFE***. "
        "Defaults to 1.0")
    parser.add_argument(
        '--suffix', '-s',
        action='store_true',
        help="Enable using suffix (`k`, `m`, `b`) as shorthand to represent "
        "thousand, million, billion. "
        "Note that the processing is done with string replace and so may require "
        "additional parentheses for correct precedence."
    )
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
        choices=('ecb', 'exch-api', 'curr-api', 'er-api'),
        default='exch-api',
        help="The backend API to query. "
        "Affects what currencies are supported. "
        "Currently supports ecb (European Central Bank), "
        "exch-api (exchange-api, formerly currency-api), "
        "curr-api (alias for exch-api), "
        "and er-api (Exchange Rate API). "
        "Defaults to exch-api")
    backendGp.add_argument(
        '--tryAll', '-a',
        action='store_true',
        help="Try all backends and report the first one that responses")
    parser.add_argument(
        '--random', '-r',
        action='store_true',
        help="Try all backends in random order. "
        "Implies --tryAll")
    args = parser.parse_args()
    args.amount = stringEval(args.amount, args.suffix)
    if args.backend == 'curr-api':
        args.backend = 'exch-api'
    if args.random:
        args.tryAll = True
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
                respTime = respJs['structure']['dimensions']['observation']\
                        [0]['values'][0]['id']
                respVal = respJs['dataSets'][0]['series']['0:0:0:0:0']['observations']\
                        ['0'][0]
                return {'rate': respVal, 'time': respTime}
            except rq.exceptions.JSONDecodeError as e:
                if resp.headers['Content-Length'] == '0':
                    raise RuntimeError({
                        'msg': "Empty response. "\
                                f"Currency may not be supported: {targetCurr}"
                    }) from e
                else:
                    raise RuntimeError({'msg': "Failed parsing response",
                                        'respContent': resp.content}) from e
        elif resp.status_code == 404:
            raise RuntimeError(
                {'msg': f"Currency not supported: {targetCurr}"})
        else:
            raise RuntimeError(
                {'msg': f"Request returned with {resp.status_code}"})
    todayDate = datetime.date.today().isoformat()
    exch1 = _ecbQueryBase(fromCurr) \
        if fromCurr.upper() != 'EUR' \
        else {'rate': 1, 'time': todayDate}
    exch2 = _ecbQueryBase(toCurr) \
        if toCurr.upper() != 'EUR' \
        else {'rate': 1, 'time': todayDate}
    return {
        'backend': 'ECB',
        'rate': exch2['rate'] / exch1['rate'],
        'time': min(exch1['time'], exch2['time'])
    }


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
        raise RuntimeError(
            {'msg': f"Currency may not be supported: {fromCurr.lower()}"})
    try:
        respJs = resp.json()
        return {
            'backend': 'exchange-api',
            'time': respJs['date'],
            'rate': respJs[fromCurr.lower()][toCurr.lower()]
        }
    except rq.exceptions.JSONDecodeError as e:
        raise RuntimeError({'msg': "Failed parsing response",
                            'respContent': resp.content}) from e
    except KeyError as e:
        raise RuntimeError({
                'msg': f"No record from {fromCurr.lower()} to {toCurr.lower()}"
            }) from e


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
                'backend': 'er-api',
                'time': str(datetime.date\
                        .fromtimestamp(respJs['time_last_update_unix'])),
                'rate': respJs['rates'][toCurr.upper()]
            }
    except rq.exceptions.JSONDecodeError as e:
        raise RuntimeError({'msg': "Failed parsing response",
                            'respContent': resp.Content}) from e


def main() -> None:
    args = getArgs()
    backendDict = {
        'exch-api': currApiQuery,
        'ecb': ecbQuery,
        'er-api': erApiQuery,
    }
    resDict: dict | None = None
    if args.tryAll:
        querySucceed = False
        for backend in (sample(tuple(backendDict.keys()), k=len(backendDict))
                        if args.random
                        else backendDict):
            print(f"Querying backend {backend}")
            try:
                resDict = backendDict[backend](args.fromCurr, args.toCurr)
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
    assert resDict is not None
    print(" ".join((
        args.fromCurr,
        formatAmount(args.amount, args),
        "->",
        args.toCurr,
        formatAmount(resDict['rate'] * args.amount, args),
        f"(on {resDict['time']}, from {resDict['backend']})"
    )))


if __name__ == '__main__':
    main()
