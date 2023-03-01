import json
import string
from tqdm import tqdm
import random

def load_sloleks(f="Sloleks2.0.MTE/sloleks_clarin_2.0-sl.tbl", only_lemmas=False):
    sloleks = set()
    with open(f, 'r') as reader:
        for line in reader:
            line = line.split('\t')
            idx = 1 if only_lemmas else 0
            sloleks.add(line[idx].strip())
    return sloleks


def load_wordlist(filename, limit="all", one_per_line=True):
    # load valid words
    wordlist = set()
    with open(filename, 'r') as reader:
        for i, line in enumerate(reader):
            if limit != "all":
                if i >= limit:
                    break
            line = line.split('\t')
            if one_per_line:
                wordlist.add(line[0].strip())
            else:
                for token in line:
                    wordlist.add(token.strip())
    return wordlist

def load_text():
    # load corpus or other text
    # za solar3, posebej preglej primere oznacene s Č in z Z
    pass

def tokenize():
    # tokenize text with classla
    pass

def oznaci():
    # check each word if valid, keep stats, mark wrong ones
    pass

def podcrtaj(tokens, validwords):
    # accepts an array/list of tokens in a sentence and a list of valid words.
    # returns bool array with non-valid words marked as True i.e. underlined
    # if validwords is None, randomly (50-50) mark a word as valid.
    podcrtani = []
    for i, t in enumerate(tokens):
        if validwords is None:
            podcrtan = t not in string.punctuation and random.random() < 0.5
        else:
            podcrtan = t not in validwords and t not in string.punctuation
            if i == 0:
                if t.lower() in validwords and not t.islower():
                    podcrtan = False
            elif tokens[i-1] in '.?!"»«„“\'' and t not in string.punctuation:
                podcrtan = t.lower() not in validwords and t not in validwords
        podcrtani.append(podcrtan)
    return podcrtani

def oceni_solar(wordlist, printnew=False):
    # posebej parser za solar3.
    # za vsak example posebej preveri orig in corr. ce je oznaka č ali z, posebej trackaj
    # te besede, id besede je podan. tako da imas potem tp, fp, tn, fn za skupno, za č in za z.
    orig_spell_mistakes = 0
    corr_spell_mistakes = 0
    total_orig, total_corr = 0, 0
    newwords = set()

    cat_spell_mistakes = {'Č': {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}, 'Z': {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}, 'any': {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}}
    with open('solar3-v1/solar3.v1.json', 'r') as reader:
        for line in tqdm(reader, total=125867):
            example = json.loads(line)
            if len(example['labels']) > 0 and len(example['corr']) > 0 and len(example['orig']) > 0:
                orig = podcrtaj(example['orig'], wordlist)
                corr = podcrtaj(example['corr'], wordlist)
                for s, word in zip(corr, example['corr']):
                    if s:
                        newwords.add(word)
                orig_spell_mistakes += sum(orig) #/len(orig)
                corr_spell_mistakes += sum(corr) #/len(corr)
                total_orig += len(orig)
                total_corr += len(corr)
                
                for cat_type in cat_spell_mistakes:
                    cat_spell_mistakes[cat_type]['fp'] += sum(corr)
                    cat_spell_mistakes[cat_type]['tn'] += len(corr) - sum(corr)
                for label in example['labels']:
                    if any(l.startswith('Č') for l in label["corr_types"]):
                        corr_type = 'Č'
                    elif any(l.startswith('Z') and not l.startswith('Z/LOČ') for l in label["corr_types"]):
                        corr_type = 'Z'
                    else:
                        corr_type = None
                    err_idx = label["idx_src"]
                    if any(orig[e] for e in err_idx):
                        cat_spell_mistakes['any']['tp'] += 1
                        if corr_type is not None:
                            cat_spell_mistakes[corr_type]['tp'] += 1
                    else:
                        cat_spell_mistakes['any']['fn'] += 1
                        if corr_type is not None:
                            cat_spell_mistakes[corr_type]['fn'] += 1
    print(f"Šolar 3: Orig WER: {round(orig_spell_mistakes/total_orig,5)} | Corr WER: {round(corr_spell_mistakes/total_corr,5)}")
    if printnew:
        with open("solar3_new_words.txt", 'w') as writer:
            for nw in newwords:
                writer.write(nw+'\n')
    for corr_type in cat_spell_mistakes:
        precision = cat_spell_mistakes[corr_type]['tp'] / (cat_spell_mistakes[corr_type]['tp'] + cat_spell_mistakes[corr_type]['fp'])
        recall = cat_spell_mistakes[corr_type]['tp'] / (cat_spell_mistakes[corr_type]['tp'] + cat_spell_mistakes[corr_type]['fn'])
        accuracy = (cat_spell_mistakes[corr_type]['tp'] + cat_spell_mistakes[corr_type]['tn']) \
            / (cat_spell_mistakes[corr_type]['tp'] + cat_spell_mistakes[corr_type]['fn'] + cat_spell_mistakes[corr_type]['fp'] + cat_spell_mistakes[corr_type]['tn'])
        cat_spell_mistakes[corr_type]['precision'] = round(precision, 2)
        cat_spell_mistakes[corr_type]['recall'] = round(recall, 2)
        cat_spell_mistakes[corr_type]['f1'] = 2*precision*recall/(precision+recall) 
        cat_spell_mistakes[corr_type]['accuracy'] = round(accuracy, 2)
    print(cat_spell_mistakes)
                
def oceni_lektor(wordlist, printnew=False):
    # posebej parser za lektor.
    orig_spell_mistakes = 0
    corr_spell_mistakes = 0
    total_orig, total_corr = 0, 0
    newwords = set()
    cat_spell_mistakes = {'P': {'tp': 0, 'fp': 0, 'fn': 0}, 'O': {'tp': 0, 'fp': 0, 'fn': 0}, 'any': {'tp': 0, 'fp': 0, 'fn': 0}}
    with open('../lektor-korpus/lektor-parsed.jsonl', 'r') as reader:
        for line in tqdm(reader, total=19935):
            example = json.loads(line)
            P = False
            O = False
            if len(example['corr_type']) > 0 and len(example['corr_tokens']) > 0 and len(example['orig_tokens']) > 0:
                orig = podcrtaj(example['orig_tokens'], wordlist)
                corr = podcrtaj(example['corr_tokens'], wordlist)

                orig_spell_mistakes += sum(orig) #/len(orig)
                corr_spell_mistakes += sum(corr) #/len(corr)
                total_orig += len(orig)
                total_corr += len(corr)
                
                for cat_type in cat_spell_mistakes:
                    cat_spell_mistakes[cat_type]['fp'] += sum(corr)
                if any(l.startswith('O-') for l in example["corr_type"]):
                        O = True
                if any(l.startswith('P-') and not l.startswith('P-Locilo') for l in example["corr_type"]):
                        P = True
                # fp
                # every underlined orig token that is also in corr tokens.
                # tp
                # every underlined orig token that is not in corr tokens.
                for s, token in zip(orig, example['orig_tokens']):
                    # if s -> positive, if not s -> negative
                    # if token in corrtokens -> false, if token not in corrtokens -> true
                    for kat, switch in [('P',P), ('O',O), ('any',True)]:
                        if switch:
                            if s and token in example['corr_tokens']:
                                cat_spell_mistakes[kat]['fp'] += 1
                            elif s and token not in example['corr_tokens']:
                                cat_spell_mistakes[kat]['tp'] += 1
                            elif not s and token in example['corr_tokens']:
                                cat_spell_mistakes[kat]['fn'] += 1
            

    print(f"Lektor: Orig WER: {round(orig_spell_mistakes/total_orig,5)} | Corr WER: {round(corr_spell_mistakes/total_corr,5)}")
    if printnew:
        with open("lektor_new_words.txt", 'w') as writer:
            for nw in newwords:
                writer.write(nw+'\n')

    for corr_type in cat_spell_mistakes:
        cat_spell_mistakes[corr_type]['precision'] = round(cat_spell_mistakes[corr_type]['tp']/(cat_spell_mistakes[corr_type]['tp']+cat_spell_mistakes[corr_type]['fp']),2)
        
        cat_spell_mistakes[corr_type]['recall'] = round(cat_spell_mistakes[corr_type]['tp']/(cat_spell_mistakes[corr_type]['tp']+cat_spell_mistakes[corr_type]['fn']), 2)
        
    print(cat_spell_mistakes)

def izbrani_spisi(wordlist, saveto):
    with open('solar3-vs/solar3.vs.json', 'r') as reader, open(saveto, 'w') as writer:
        writer.write('<html>\n<head>\n<style type="text/css">\np.text {color:#202020}\nspan.podcrtan {color:#DD0022; text-decoration: underline; text-decoration-color:#DD0022}\nspan.docid {color:#202020; background-color:#AAFFFF}\n</style>\n</head>\n<body>\n')
        prev_example_id = -1
        for line in reader:
            example = json.loads(line)
            podcrtani = podcrtaj(example['orig'], wordlist)
            example_id = example['id_doc']
            spis = ""
            if prev_example_id != example_id:
                spis += f"\n<hr />\n<span class=\"docid\">{example_id}:</span>\n"
                prev_example_id = example_id
            spis += f"<p class=\"text\">"
            for s, word in zip(podcrtani, example['orig']):
                if s:
                    spis += f'<span class="podcrtan">{word}</span> '
                else:
                    spis += f'{word} '
            writer.write(spis+'</p>\n')
        writer.write('</body>\n</html>\n')

def main():
    sloleks2 = load_sloleks()
    print("Sloleks 2")
    oceni_solar(sloleks2)
    oceni_lektor(sloleks2)
    print()
    sloleks3 = load_sloleks("sloleks3/sloleks3-oldformat.tsv")
    print("Sloleks 3.0")
    oceni_solar(sloleks3)
    oceni_lektor(sloleks3, printnew=True)
    for wordlistf in ['word-list.words.no_sloleks.include-maks-ucbeniki-trendi-kas.exclude-gigafida.txt', 'word-list.words.no_sloleks.include-maks-ucbeniki-trendi-kas.exclude-.txt', 'maks-ucbeniki-gigafida-kas.cross-word-list.words.no_sloleks.txt']:
        for limit in [100, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 'all']:
            print()
            wordlist = load_wordlist(wordlistf, limit=limit)
            newlist = sloleks2 | wordlist
            print(f"Sloleks2 + top {limit} {wordlistf}")
            oceni_solar(newlist)
            oceni_lektor(newlist)
        
def main2():
    sloleks3 = load_sloleks("sloleks3/sloleks3-oldformat.tsv")
    hunspell = load_wordlist("libreoffice/sl_SI.list.filtered.txt")
    # unmunch sl_SI.dic sl_SI.aff | grep -v '<' > sl_SI.list.filtered.txt
    izbrani_spisi(sloleks3, 'podcrtani_spisi.html')
    izbrani_spisi(hunspell, 'podcrtani_spisi_hunspell.html')
    print('sloleks3')
    oceni_solar(sloleks3)
    print('hunspell')
    oceni_solar(hunspell)
    print('random')
    oceni_solar(None)
    #oceni_lektor(sloleks3)
    #oceni_lektor(hunspell)
        
if __name__ == "__main__":
    main2()
