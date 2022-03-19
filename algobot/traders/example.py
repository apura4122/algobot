
from collections import subtract
popsize = 10
dimensions = 4
crossp = 0.6

combos = {'Interval':['1 day'],'strategy' : {'Supertrend':{'Buy': (1,2,1), 'Sell':(1,3,2), 'Parameter': ['Close'], 'ATR':(2,3,4)}}}

mutated = {'Interval':['1 day'],'strategy' : {'Supertrend':{'Buy': (0,3,1), 'Sell':(4,5,2), 'Parameter': ['Close'], 'ATR':(2,3,4)}}}
combose = mutated.substract(combos)
sete = list(combos.get('strategy',{}).get('Supertrend',{}).values())
sete = [x[:-1] for x in sete]
print(combose)