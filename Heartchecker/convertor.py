import pandas as pd
import json
if __name__=="__main__":

 data_csv=pd.read_csv("./data/coronary_artery_disease.csv")
 with(open('./data/coronary_artery_disease.json',"w") as f):
        json.dump(data_csv.to_dict(orient="records"),f)
