# functions to update a database with a scheduler
import pickle
import random
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta, FR

from itertools import combinations
from collections import OrderedDict, defaultdict

import pymongo

import os

# history = OrderedDict()
# history["07/25/2022_8/05/2022"] =  frozenset({frozenset({"Mohar", "Kirtiraj", "Jie"}), 
#                       frozenset({"Kelly", "Kyle C.", "Jonathan"}),
#                       frozenset({"Eunice", "Denis", "Carly"}),
#                       frozenset({"Bridget", "Kyle B.", "Piyush"}),
#                       frozenset({"Cody", "Stan", "Bud"})})
    
# history["08/08/2022_08/19/2022"] = frozenset({frozenset({"Jie", "Kelly", "Bud"}),
#                     frozenset({"Denis", "Kirtiraj", "Kyle B.", "Stan"}),
#                     frozenset({"Bridget", "Carly", "Mohar"}),
#                     frozenset({"Eunice", "Piyush", "Cody", "Jonathan"})})




# 16 people, 4 groups of 4
# 15 people, 5 groups of 3
# 14 people, 2 groups of 4, 2 groups of 3
# 13 people, 1 group of 4, 3 groups of 3

def convert_from_fz_to_str(g):
    res = ""
    for elem in list(g):
        res += ",".join(list(elem))
        res += "; "
    return res

def convert_from_str_to_fz(s):
    res = s.split("; ")[:-1]
    res2 = []
    for elem in res:
        res2.append(frozenset(elem.split(",")))
    return frozenset(res2)

def read_in_history():
    client = pymongo.MongoClient(os.environ.get("DATABASE_URL"))
    print("read data from mongo")

    db = client["peers"]
    collection = db["a"]

    history_from_mongo = list(collection.find())
    print(history_from_mongo)
    # sort history
    newlist = sorted(history_from_mongo, key=lambda d: datetime.strptime(d['time_period'].split("_")[0], "%m/%d/%Y"))
    
    history_dict = OrderedDict()
    for data in newlist:
        history_dict[data["time_period"]] = convert_from_str_to_fz(data["grouping"])
    print(newlist)
    return history_dict, newlist[-1]
    
def get_pairs_so_far(history):
    
    pairs_so_far = defaultdict(int)
    
    for time, val in history.items():
        for elem in list(val):
            for pair in combinations(elem, 2):
                pairs_so_far[frozenset(pair)] += 1
                
        
    return pairs_so_far


def assign_score(candidate, pairs_so_far):
    score = 0
    for elem in list(candidate):
        for pair in combinations(elem, 2):
            score += pairs_so_far[frozenset(pair)] 
    return score
    
def choose_group_splits(num_people):
    if num_people%4 == 0:
        return {"four": num_people//4, "three": 0}
    elif num_people%3 == 0:
        return {"four": 0, "three": num_people//3}
    else:
        split_strategy = {"four": 0, "three": 0}
        while num_people %3  != 0:
            num_people -= 4
            split_strategy["four"] += 1
        
        while num_people != 0:
            num_people -= 3
            split_strategy["three"] += 1
        
        return split_strategy
    


def generate_random_groups(people, pairs_so_far, n=1000):
    num_people = len(people)
    split_strategy = choose_group_splits(num_people)
    
    sample_score_dict = dict()
    repeat_samples_dict = defaultdict(int)
    for _ in range(n):
        candidate_order = random.sample(people, num_people)
        
        g4 = candidate_order[0:split_strategy["four"]*4] 
        
        g4_2d = []
        i= 0
        while i < len(g4):
            g4_2d.append(frozenset(g4[i: i+4]))
            i+=4
        if split_strategy["three"] != 0:
            # get remaining part of list
            g3 = candidate_order[split_strategy["four"]*4:] 
            g3_2d = []
            i = 0
            while i < len(g3):
                g3_2d.append(frozenset(g3[i: i+3]))
                i+=3
        
        candidate = frozenset(g4_2d + g3_2d)
        sample_score_dict[candidate] = assign_score(candidate, pairs_so_far)
        repeat_samples_dict[candidate] += 1

    return sample_score_dict, repeat_samples_dict

def choose_best_sampled_group(sample_score_dict):
    min_score = min(sample_score_dict.values())
    for k, v in sample_score_dict.items():
        if v == min_score:
            return k

def write_to_mongo(time_period, grouping, score):
    client = pymongo.MongoClient(os.environ.get("DATABASE_URL"))

    db = client["peers"]
    collection = db["a"]

    record = {
    "time_period":  time_period,
    "grouping":  grouping,
    "score": score
    }

    collection.insert_one(record)
    # testing = collection.find_one()
    # print(testing)
    print("write to mongo")

    return

# read and write to database somehow
def main():
    
    people = ["Bridget", "Bud", "Carly", "Cody", "Denis", "Eunice", "Jie", "Jonathan", "Kelly", "Kirtiraj", "Kyle B.", "Kyle C.", "Mohar", "Piyush", "Stan"]

    history, most_recent_group = read_in_history()
    
    most_recent_end_date = most_recent_group["time_period"].split("_")[-1] 
    
    today = date.today().strftime("%m/%d/%Y")
    # so the monday after the friday of the most recent time period
    date_to_update = (datetime.strptime(most_recent_end_date, "%m/%d/%Y") + timedelta(days=3)).strftime("%m/%d/%Y")
    
    if today == date_to_update: #"08/21/2022"

        pairs_so_far = get_pairs_so_far(history)
        
        # n param determines number of sample groupings taken
        scores_dict, freq = generate_random_groups(people = people, pairs_so_far = pairs_so_far, n = 1000)
        
        final_group = choose_best_sampled_group(sample_score_dict = scores_dict)
        
        best_score_of_samples = scores_dict[final_group]
        # print(f"best score sampled: {best_score_of_samples}")
        
        new_grouping = convert_from_fz_to_str(final_group)
        
        today = date.today()
        # get the next next Friday
        end_date = today + relativedelta(weekday=FR(+2))
        today_mdy = today.strftime("%m/%d/%Y")
        end_mdy = end_date.strftime("%m/%d/%Y")
        
        time_period = today_mdy + "_" + end_mdy
        
        write_to_mongo(time_period = time_period, grouping = new_grouping, score = best_score_of_samples)
        
        return

if __name__ == "__main__":
    main()
    