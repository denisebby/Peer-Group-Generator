import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import plotly.express as px
import dash_bootstrap_components as dbc

import pandas as pd

from itertools import islice

import pymongo

from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta


# Define app
# VAPOR, LUX, QUARTZ
# external_stylesheets=[dbc.themes.QUARTZ]
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], meta_tags=[{'name': 'viewport','content': 'width=device-width, initial-scale=1.0'}])

server = app.server
# Define callbacks

navbar = dbc.NavbarSimple(
    # brand="DSG Peer Group Generator",
    brand_href="#",
    color="success",
    dark=True,
    id = "navbar-example-update"
)

# description = """
# TODO: fill in description
# """

print("hi from global")

# card_content = [
#     dbc.CardBody(
#         [
#             html.H5("Card title", className="card-title"),
#             html.P(
#                 "This is some card content that we'll reuse",
#                 className="card-text",
#             ),
#         ]
#     ),
# ]

# cards = html.Div(
#     [
#         dbc.Row([html.H1("8-22-22 to 9-2-22")]),
#         dbc.Row(
#             [
#                 dbc.Col(dbc.Card(card_content, color="primary", inverse=True)),
#                 dbc.Col(
#                     dbc.Card(card_content, color="secondary", inverse=True)
#                 ),
#                 dbc.Col(dbc.Card(card_content, color="info", inverse=True)),
#             ],
#             className="mb-4",
#         ),
#         dbc.Row(
#             [
#                 dbc.Col(dbc.Card(card_content, color="success", inverse=True)),
#                 dbc.Col(dbc.Card(card_content, color="warning", inverse=True)),
#                 dbc.Col(dbc.Card(card_content, color="danger", inverse=True)),
#             ],
#             className="mb-4",
#         ),
#         dbc.Row(
#             [
#                 dbc.Col(dbc.Card(card_content, color="light")),
#                 dbc.Col(dbc.Card(card_content, color="dark", inverse=True)),
#             ]
#         ),
#     ]
# )


 # "8-22-22 to 9-2-22"


########## UTILITY FUNCTIONS ###############################
def generate_cards(date, groups, card_num_cols):
    
    len_groups = len(list(groups))
    
    # Use islice
    def convert(listA, len_2d):
        res = iter(listA)
        return [list(islice(res,i)) for i in len_2d]
    
    # this list helps dynamically display layout of the cards
    res = convert(list(groups), [card_num_cols]*(len_groups//card_num_cols) + [len_groups%card_num_cols])
    
    # get card body
    cards_body = []
    for r in res:
        row_list = []
        for c in list(r):
            
            card_content = [dbc.CardBody(html.H5(", ".join(list(c)), className="card-title"))]
            
            row_list.append(dbc.Col(dbc.Card(card_content, color = "success", inverse=True), width = 12//card_num_cols))
            
        cards_body.append(dbc.Row(row_list, className="mb-4", justify="center"))
    
    cards = html.Div( [dbc.Row([html.H1(date)])]+ cards_body)

    return cards

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

#############################################################

cards = html.Div(id="cards")


# app.layout = [navbar, dbc.Container()]
app.layout = html.Div([ dcc.Store(id="navbar-example-input", data=""), navbar, dcc.Store(id="cards-input", data=""),
                       dbc.Container([cards], style = {"margin-top": "5%", "margin-bottom": "5%"})])


@app.callback(
    Output("cards", "children"), [Input("cards-input", "data")]
)
def get_data_and_cards(data_input):
    client = pymongo.MongoClient("mongodb+srv://denisebby:giraffe2Dorne@cluster0.jkf2qtl.mongodb.net/?retryWrites=true&w=majority")
    print("read data from mongo")

    db = client["peers"]
    collection = db["a"]

    history_from_mongo = list(collection.find())
    
    # sort history
    newlist = sorted(history_from_mongo, key=lambda d: datetime.strptime(d['time_period'].split("_")[0], "%m/%d/%Y")) 

    date = " to ".join(newlist[-1]["time_period"].split("_"))
    
    # frozen set of frozen sets, get most recent grouping
    groups = convert_from_str_to_fz(newlist[-1]["grouping"])

    # can parametrize this later if necessary
    card_num_cols = 3
    
    # generate cards
    cards = generate_cards(date = date, groups = groups, card_num_cols = card_num_cols)
    
    return cards
    
    
    
    
    
    # return [
    #     textbox(x, box="user") if i % 2 == 0 else textbox(x, box="AI")
    #     for i, x in enumerate(chat_history.split("<split>")[:-1])
    # ]
    

@app.callback(
    Output("navbar-example-update", "brand"), [Input("navbar-example-input", "data")]
)
def get_example_update(data_input):
    client = pymongo.MongoClient("mongodb+srv://denisebby:giraffe2Dorne@cluster0.jkf2qtl.mongodb.net/?retryWrites=true&w=majority")
    print("read data from mongo - example")

    db = client["peers"]
    collection = db["example"]
    
    data_from_mongo = list(collection.find())
    
    return data_from_mongo[0]["navbar_title"]


    
if __name__=='__main__':
    app.run_server(debug=True, port=8005)