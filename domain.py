import re, collections
POS={'great','excellent','good','love','amazing','fast','reliable','best','helpful','quality','happy'}
NEG={'bad','poor','hate','slow','broken','worst','expensive','terrible','disappointed','rude','delay'}
def analyze(text):
    words=re.findall(r"[a-z]+",text.lower()); score=0; hits=[]
    for i,w in enumerate(words):
        value=1 if w in POS else -1 if w in NEG else 0
        if value:
            if any(x in {'not','never','no'} for x in words[max(0,i-2):i]): value=-value
            score+=value; hits.append(w)
    return {'sentiment':'Positive' if score>0 else 'Negative' if score<0 else 'Neutral','score':score,'keywords':hits}
def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,user_id INTEGER,brand TEXT,text TEXT,sentiment TEXT,score INTEGER)')
def dispatch(db,user,method,path,data):
    if path=='/api/analyze' and method=='POST':
        brand=str(data['brand']).strip(); texts=data['reviews']
        if not brand or len(brand)>80 or not isinstance(texts,list) or not 1<=len(texts)<=500: raise ValueError('Brand and 1–500 reviews required')
        results=[]
        for text in texts:
            if not isinstance(text,str) or not text.strip() or len(text)>5000: raise ValueError('Each review must contain 1–5000 characters')
            results.append((text.strip(),analyze(text)))
        for text,result in results: db.execute('INSERT INTO reviews(user_id,brand,text,sentiment,score) VALUES(?,?,?,?,?)',(user['id'],brand,text,result['sentiment'],result['score']))
        return {'results':[dict(text=t,**r) for t,r in results]}
    if path=='/api/dashboard' and method=='GET':
        rows=[dict(r) for r in db.execute('SELECT * FROM reviews WHERE user_id=? ORDER BY id DESC',(user['id'],))]
        brands={}
        for row in rows:
            b=brands.setdefault(row['brand'],{'Positive':0,'Negative':0,'Neutral':0,'total':0}); b[row['sentiment']]+=1; b['total']+=1
        for b in brands.values(): b['positive_percent']=round(100*b['Positive']/b['total'])
        return {'reviews':rows,'brands':brands,'model':'English lexicon baseline; not an LLM. Sarcasm and complex language may be misclassified.'}
    if path=='/api/delete' and method=='POST':
        db.execute('DELETE FROM reviews WHERE id=? AND user_id=?',(data['id'],user['id'])); return {'ok':True}
    raise ValueError('Unknown operation')
