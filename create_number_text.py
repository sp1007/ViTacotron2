from tacotron2.text.vi_number_and_units import normalize_vi
from random import randrange


print("Start generate vietnamese number strings")

with open("training_data/vietnamese_number.txt", 'w', encoding='utf-8') as f: 
    for i in range(20000):
        n = randrange(1000000000, 2000000000)
        f.write(normalize_vi(str(n)) + '\n')

print("done!")