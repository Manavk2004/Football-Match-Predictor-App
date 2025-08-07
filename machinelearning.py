import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score

matches = pd.read_csv("matches.csv", index_col=0)

# Remove duplicate header rows that got mixed in with the data
matches = matches[matches["Date"] != "Date"]

# Reset index after filtering
matches = matches.reset_index(drop=True)

matches["Date"] = pd.to_datetime(matches["Date"])


numeric_cols = ["GF", "GA", "Sh", "SoT", "Dist", "FK", "PK", "PKatt", "xG", "xGA", "Poss", "Attendance"]
for col in numeric_cols:
    if col in matches.columns:
        matches[col] = matches[col].astype(str).str.extract(r'(\d+)')[0]
        matches[col] = pd.to_numeric(matches[col], errors='coerce')

matches['venue_code'] = matches['Venue'].astype('category').cat.codes
matches["opp_code"] = matches["Opponent"].astype('category').cat.codes
matches["hour"] = matches["Time"].str.replace(":.+", "", regex=True).astype("int")
matches["day_code"] = matches["Date"].dt.dayofweek
matches["target"] = (matches["Result"] == "W").astype("int")


rf = RandomForestClassifier(n_estimators=50,
                            min_samples_split=10,
                            random_state=1)

train = matches[matches["Date"] < '2023-01-01']
test = matches[matches["Date"] > '2023-01-01']
predictors = ["venue_code", "opp_code", "hour", "day_code"]
rf.fit(train[predictors], train["target"])
preds = rf.predict(test[predictors])
accuracy = accuracy_score(test["target"], preds)
print(accuracy)
#Initial accuracy score was 0.5973973159821065

combined = pd.DataFrame(dict(actual=test["target"], predictions=preds))
print(combined)


crosstab = pd.crosstab(index=combined["actual"], columns=combined["predictions"])  
print("The crosstab", crosstab)
#When predicting losses/draws, it predicts it correctly more times than not
#When predicting wins, it predicts it correctly more times than not

precision = precision_score(test["target"], preds)
print(precision)

#Precision score is 0.5255391600454029 which shows that its predicting wins correctly more times than not

grouped_matches = matches.groupby("Team")
print("Grouped matches", grouped_matches)
group = grouped_matches.get_group("ManchesterCity")
print(group)


def rolling_averages(group, cols, new_cols):
    group = group.sort_values("Date")
    rolling_stats = group[cols].rolling(3, closed="left").mean()
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

cols = ["GF", "GA", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]
new_cols = [f"{c}_rolling" for c in cols]
matches_rolling = matches.groupby("Team").apply(lambda x: rolling_averages(x, cols, new_cols), include_groups=False)
matches_rolling = matches_rolling.reset_index()
matches_rolling = matches_rolling.drop('level_1', axis=1)


def make_predictions(data, predictors):
    train = data[data["Date"] < '2024-01-01']
    print("training", train)
    test = data[data["Date"] >= '2024-01-01']
    print("test", test)
    
    print("matches rolling", matches_rolling)
    
    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], predicted=preds), index=test.index)
    
    if "Team" in data.columns and "Opponent" in data.columns:
        combined = combined.merge(data[["Team", "Opponent", "Date", "Result"]], left_index=True, right_index=True)
    
    precision = precision_score(test["target"], preds)
    return combined, precision



combined, precision = make_predictions(matches_rolling, predictors + new_cols)



class MissingDict(dict):
    __missing__ = lambda self, key: key

map_values ={
    "Brighton and Hove Albion": "Brighton",
    "Manchester United": "Machester Utd",
    "Newcastle United": "Newcastle Utd",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves"
}

mapping = MissingDict(**map_values)
print(mapping["Newcastle United"])

print("First combined", combined)

combined["New_team"] = combined["Team"].map(mapping)
print(combined)

merged = combined.merge(combined, left_on=["Date", "New_team"], right_on=["Date", "Opponent"])
print(merged)

predictions = merged[(merged["predicted_x"] == 1) & (merged["predicted_y"] == 0)]["actual_x"].value_counts()
print(predictions)