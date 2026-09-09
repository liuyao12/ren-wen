import json,re,pathlib
R=pathlib.Path.cwd();c=json.loads((R/'data/catalog.json').read_text());old=json.loads((R/'data/editorial/eccp-batch-01.json').read_text())
people=[]
def person(id,label,terms,**extra):
 people.append(dict(id='person-'+id,label=label,terms=terms,**extra))
person('zeng-guofan','曾國藩',['TSÊNG Kuo-fan','Tsêng Kuo-fan','曾國藩','Tsêng','伯涵','滌生'],entry='Tsêng Kuo-fan')
new=[
 ('zeng-yuping','曾玉屏',["Tsêng Yü-p'ing",'曾玉屏','星岡'],{'years':[1774,1849],'zi':['星岡']}),
 ('zeng-linshu','曾麟書',['Tsêng Lin-shu','曾麟書','竹亭'],{'years':[1790,1857],'zi':['竹亭']}),
 ('hong-xiuquan','Hung Hsiu-ch’üan',["Hung Hsiu-ch'üan"],{'entry':"Hung Hsiu-ch'üan"}),
 ('xiang-rong','Hsiang Jung',['Hsiang Jung'],{'entry':'Hsiang Jung'}),
 ('luo-zenan','Lo Tsê-nan',['Lo Tsê-nan'],{'entry':'Lo Tsê-nan'}),
 ('yang-yuebin','Yang Yüeh-pin',['Yang Yüeh-pin'],{'discussedUnder':"P'êng Yü-lin"}),
 ('tachibu',"T'a-ch'i-pu",["T'a-ch'i-pu"],{'entry':"T'a-ch'i-pu",'undivided':True}),
 ('jierhanga','Chi-êr-hang-a',['Chi-êr-hang-a'],{'entry':'Chi-êr-hang-a','undivided':True}),
 ('lin-qirong','林啓容',["Lin Ch'i-jung",'林啓容'],{'years':[None,1858]}),
 ('hu-linyi','Hu Lin-i',['Hu Lin-i'],{'entry':'Hu Lin-i'}),
 ('shi-dakai',"Shih Ta-k'ai",["Shih Ta-k'ai"],{'entry':"Shih Ta-k'ai"}),
 ('li-xubin','Li Hsü-pin',['Li Hsü-pin'],{'entry':'Li Hsü-pin'}),
 ('li-xiucheng',"Li Hsiu-ch'êng",["Li Hsiu-ch'êng"],{'entry':"Li Hsiu-ch'êng"}),
 ('bao-chao',"Pao Ch'ao",["Pao Ch'ao"],{'entry':"Pao Ch'ao"}),
 ('wang-shiduo','Wang Shih-to',['Wang Shih-to'],{'entry':'Wang Shih-to'}),
 ('mo-youzhi','Mo Yu-chih',['Mo Yu-chih'],{'entry':'Mo Yu-chih'}),
 ('rong-hong','Jung Hung',['Jung Hung','Yung Wing','Jung'],{'entry':'Jung Hung'}),
 ('ma-xinyi','Ma Hsin-i',['Ma Hsin-i'],{'entry':'Ma Hsin-i'}),
 ('gu-yanwu','Ku Yen-wu',['Ku Yen-wu'],{'entry':'Ku Yen-wu'}),
 ('zhang-yuzhao','Chang Yü-chao',['Chang Yü-chao'],{'entry':'Chang Yü-chao'}),
 ('liu-shengmu','Liu Shêng-mu',['Liu Shêng-mu'],{'discussedUnder':'Chang Yü-chao'}),
 ('zeng-guohuang','曾國潢',['Tsêng Kuo-huang','曾國潢','澄侯'],{'years':[1820,1885],'zi':['澄侯']}),
 ('zeng-guohua','曾國華',['Tsêng Kuo-hua','曾國華','温甫'],{'years':[1822,1858],'zi':['温甫']}),
 ('zeng-guobao','曾國葆',['Tsêng Kuo-pao','曾國葆','曾貞榦','季洪','事恆'],{'years':[1828,1863],'zi':['季洪','事恆']}),
 ('zeng-guolan','曾國蘭',['Tsêng Kuo-lan','曾國蘭'],{}),
 ('wang-pengyuan','王鵬遠',["Wang P'êng-yüan",'王鵬遠'],{}),
 ('zeng-guohui','曾國蕙',['Tsêng Kuo-hui','曾國蕙'],{}),
 ('wang-daipin','王待聘',["Wang Tai-p'in",'王待聘'],{}),
 ('zeng-guozhi','曾國芝',['Tsêng Kuo-chih','曾國芝'],{}),
 ('zhu-yongchun','朱詠春',["Chu Yüng-ch'un",'朱詠春'],{'note':'Brother-in-law of 曾國藩, not the earlier author 朱用純.'}),
 ('zeng-jihong','曾紀鴻',['Tsêng Chi-hung','曾紀鴻','栗諴'],{'years':[1848,1881],'zi':['栗諴']}),
 ('zeng-jijing','曾紀靜',['Tsêng Chi-ching','曾紀靜'],{}),
 ('yuan-bingzhen','袁秉楨',["Yüan Ping-chên",'袁秉楨'],{}),
 ('zeng-jiyao','曾紀耀',['Tsêng Chi-yao','曾紀耀'],{}),
 ('chen-yuanji','陳遠濟',["Ch'ên Yüan-chi",'陳遠濟'],{}),
 ('zeng-jichen','曾紀琛',["Tsêng Chi-ch'ên",'曾紀琛'],{}),
 ('luo-zhaosheng','羅兆升',['Lo Chao-shêng','羅兆升'],{}),
 ('zeng-jifen','曾紀芬',['Tsêng Chi-fên','曾紀芬'],{'years':[1852,None]}),
 ('nie-jigui','聶緝槼',["Nieh Ch'i-kuei",'聶緝槼'],{}),
 ('li-yuandu','Li Yüan-tu',['Li Yüan-tu'],{'entry':'Li Yüan-tu'}),
 ('li-shuchang',"Li Shu-ch'ang",["Li Shu-ch'ang"],{'entry':"Li Shu-ch'ang"}),
 ('xue-fucheng',"Hsüeh Fu-ch'êng",["Hsüeh Fu-ch'êng"],{'entry':"Hsüeh Fu-ch'êng"}),
 ('yu-yue','Yü Yüeh',['Yü Yüeh'],{'entry':'Yü Yüeh'}),
 ('guanwen','Kuan-wên',['Kuan-wên'],{'entry':'Kuan-wên','undivided':True}),
 ('wang-kaiyun','王闓運',["Wang K'ai-yün",'王闓運'],{}),
 ('wang-dingan','王定安',['Wang Ting-an','王定安'],{}),
 ('mcclellan-jw','J. W. McClellan',['McClellan, J. W.'],{}),
 ('h-b-morse','Hosea Ballou Morse',['Morse, H. B.'],{'sourceURL':'https://en.wikisource.org/wiki/Author:Hosea_Ballou_Morse'}),
 ('william-james-hail','William James Hail',['Hail, William James'],{'sourceURL':'https://en.wikisource.org/wiki/Author:William_James_Hail'}),
 ('jiang-xingde','蔣星德',['Chiang Hsing-tê','蔣星德'],{}),
 ('teng-ssu-yu','Têng Ssŭ-yü',['Têng Ssŭ-yü'],{})
]
for x,l,t,e in new:person(x,l,t,**e)
existing={p['id']:p for p in old['people']}
keep=['jiang-zhongyuan','luo-bingzhang','guo-songtao','peng-yulin','senggelinqin','lin-fengxiang','zeng-guoquan','zuo-zongtang','li-hongzhang','chonghou','zeng-jize','zeng-jichun','guo-gangji','yixin']
for id in keep:
 p=existing['person-'+id];people.append({**p,'terms':[t for t in p['terms'] if len(t)>5 or re.search('[\u3400-\u9fff]',t)]})
for p in people:
 if p['id'] in ['person-guo-gangji','person-zeng-jichun']:
  p['terms']+=['郭剛基' if p['id']=='person-guo-gangji' else '曾紀純']
works=[]
def work(id,title,terms,kind='book',creators=None,**kw):
 works.append({'id':'work-'+id,'title':title,'terms':terms,'kind':kind,'creators':creators or [],**kw})
z=[{'person':'person-zeng-guofan','role':'author'}]
work('zeng-wenzheng-quanji','曾文正公全集',["曾文正公全集 Tsêng Wên-chêng kung ch'üan-chi","曾文正公全集","Tsêng Wên-chêng kung ch'üan-chi"],creators=z,extent='174 chüan',publication='1876, as reported by ECCP')
work('zeng-wenzheng-nianpu','曾國藩年譜（ECCP 所述十二卷本）',["nien-p'u"],kind='biographical-chronology',passages=[14],extent='12 chüan',note='Descriptive editorial title. Compiled by his pupils; exact Chinese title is not transcribed in ECCP.')
for id,title,terms in [
 ('zeng-dashiji','大事記',['大事記 Ta-shih chi','Ta-shih chi']),
 ('zeng-shoushu-riji','手書日記',['手書日記 Shou-shu jih-chi','Shou-shu jih-chi']),
 ('zeng-wenzheng-jiashu','Tsêng Wên-chêng kung chia-shu',['Tsêng Wên-chêng kung chia-shu','家書']),
 ('zeng-jiaxun','家訓',['家訓 Chia-hsün','Chia-hsün']),
 ('zeng-jiwaiwen','Tsêng Wen-chêng kung chi wai-wên',['Tsêng Wen-chêng kung chi wai-wên','集外文']),
 ('zenghu-zhibing-yulu','曾胡治兵語錄',['曾胡治兵語錄 Tsêng-Hu chih-ping yü-lu','Tsêng-Hu chih-ping yü-lu']),
 ('zeng-jiayan-chao',"Tsêng Wên-chêng kung chia-yen ch'ao",["Tsêng Wên-chêng kung chia-yen ch'ao",'嘉言鈔']),
 ('zeng-xuean','Tsêng Wên-chêng kung hsüeh-an',['Tsêng Wên-chêng kung hsüeh-an','學案']),
 ('jiangsu-jianfu-quanan','江蘇減賦全案',["江蘇減賦全案 Kiangsu chien-fu ch'üan-an","Kiangsu chien-fu ch'üan-an"]),
 ('jiangxi-quansheng-yutu','江西全省輿圖',["江西全省輿圖 Kiangsi ch'üan-shêng yü-t'u","Kiangsi ch'üan-shêng yü-t'u"]),
 ('chongde-laoren-nianpu','崇德老人八十自訂年譜',["崇德老人八十自訂年譜 Ch'ung-tê lao-jên pa-shih tzŭ-ting nien-p'u","Ch'ung-tê lao-jên pa-shih tzŭ-ting nien-p'u"]),
 ('tianyue-shanguan-wenchao',"T'ien-yüeh shan-kuan wên-ch'ao",["T'ien-yüeh shan-kuan wên-ch'ao"]),
 ('yangzhishuwu-wenji','Yang-chih shu-wu wên-chi',['Yang-chih shu-wu wên-chi']),
 ('zhuozunyuan-conggao',"Cho-tsun-yüan ts'ung-kao",["Cho-tsun-yüan ts'ung-kao"]),
 ('yongan-wenbian','Yung-an wên-pien',['Yung-an wên-pien']),
 ('chunzaitang-zawen',"Ch'un-tsai-t'ang tsa-wên",["Ch'un-tsai-t'ang tsa-wên"]),
 ('jiaoping-yuefei-fanglue','Chiao-ping Yüeh-fei fang-lüeh',['Chiao-ping Yüeh-fei fang-lüeh']),
 ('pingding-yuefei-jilue',"P'ing-ting Yüeh-fei chi-lüeh",["P'ing-ting Yüeh-fei chi-lüeh"]),
 ('xiangjun-zhi','湘軍志',['湘軍志 Hsiang-chün chih','Hsiang-chün chih']),
 ('xiangjun-ji','湘軍記',['湘軍記 Hsiang-chün chi','Hsiang-chün chi']),
 ('qiuquezhai-diziji','求闕齋弟子記',["求闕齋弟子記 Ch'iu-ch'üeh-chai ti-tzŭ-chi","Ch'iu-ch'üeh-chai ti-tzŭ-chi"]),
 ('xianfeng-bingshi-yueri','咸豐三年以來兵事月日',['咸豐三年以來兵事月日 Hsien-fêng san-nien i-lai ping-shih yüeh-jih','Hsien-fêng san-nien i-lai ping-shih yüeh-jih']),
 ('tongzhi-shangjiang-xianzhi','同治上江兩縣志',["同治上江兩縣志 T'ung-chih Shang Chiang liang-hsien chih","T'ung-chih Shang Chiang liang-hsien chih"]),
 ('li-xiucheng-gongzhuang',"Li Hsiu-ch'êng kung-chuang",["Li Hsiu-ch'êng kung-chuang"]),
 ('story-of-shanghai','The Story of Shanghai',['The Story of Shanghai']),
 ('my-life-china-america','My Life in China and America',['My Life in China and America']),
 ('international-relations-chinese-empire','The International Relations of the Chinese Empire',['The International Relations of the Chinese Empire']),
 ('zeng-taiping-hail','Tsêng Kuo-fan and the Taiping Rebellion',['Tsêng Kuo-fan and the Taiping Rebellion']),
 ('zhijietang-congke','直介堂叢刻',["直介堂叢刻 Chih-chieh-t'ang ts'ung-k'o","Chih-chieh-t'ang ts'ung-k'o"]),
 ('zeng-shengping-shiye','曾國藩之生平及事業',["曾國藩之生平及事業 Tsêng Kuo-fan chih shêng-p'ing chi shih-yeh","Tsêng Kuo-fan chih shêng-p'ing chi shih-yeh"]),
 ('dagongbao','Ta-kung pao',['Ta-kung pao']),
 ('wenxue-fukan',"Wên-hsüeh fu-k'an",["Wên-hsüeh fu-k'an"]),
 ('wenzhe-jikan','文哲季刊',["文哲季刊 Wên-chê chi-k'an","Wên-chê chi-k'an"]),
 ('shida-yuekan','師大月刊',["師大月刊 Shih-ta yüeh-k'an","Shih-ta yüeh-k'an"])
]:work(id,title,terms)
roles={'zeng-shoushu-riji':'zeng-guofan','zeng-wenzheng-jiashu':'zeng-guofan','zeng-jiaxun':'zeng-guofan','zeng-jiwaiwen':'zeng-guofan','chongde-laoren-nianpu':'zeng-jifen','tianyue-shanguan-wenchao':'li-yuandu','yangzhishuwu-wenji':'guo-songtao','zhuozunyuan-conggao':'li-shuchang','yongan-wenbian':'xue-fucheng','chunzaitang-zawen':'yu-yue','xiangjun-zhi':'wang-kaiyun','xiangjun-ji':'wang-dingan','qiuquezhai-diziji':'wang-dingan','li-xiucheng-gongzhuang':'li-xiucheng','story-of-shanghai':'mcclellan-jw','my-life-china-america':'rong-hong','international-relations-chinese-empire':'h-b-morse','zeng-taiping-hail':'william-james-hail','zhijietang-congke':'liu-shengmu','zeng-shengping-shiye':'jiang-xingde'}
for w in works:
 key=w['id'][5:]
 if key in roles:w['creators']=[{'person':'person-'+roles[key],'role':'cited author'}]
 if key in ['dagongbao','wenxue-fukan','wenzhe-jikan','shida-yuekan']:w['kind']='periodical'
scoped=[{'entity':'person-luo-zenan','terms':['Lo'],'passages':[3,4]},{'entity':'person-jiang-zhongyuan','terms':['Chiang'],'passages':[3,4]},{'entity':'person-li-hongzhang','terms':['Li'],'passages':[11]},{'entity':'person-yizhu','terms':['the Emperor'],'passages':[3]}]
person('feng-guifen','Fêng Kuei-fên',['Fêng Kuei-fên'],entry='Fêng Kuei-fên')
spec={'schemaVersion':1,'id':'eccp-zeng-guofan','entry':'Tsêng Kuo-fan','subject':'person-zeng-guofan','author':'Têng Ssŭ-yü','people':people,'works':works,'scoped':scoped,'unresolved':[{'passage':12,'text':'the Emperor','reason':'Retrospective discussion does not establish a unique reign; do not silently choose Xianfeng or Tongzhi.'}],'editorialNotes':['Preserve apparent transcription errors exactly, including ittempted, tbr, oten come, rook and la addition; do not silently emend the source.','Lo and Chiang in paragraph 4 follow the source account, even if their historical role/date needs checking.','No second biography is imported in this operation. External openings are only identification evidence.']}
(R/'data/editorial/eccp-zeng-guofan.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
print(len(people),'people',len(works),'works')
