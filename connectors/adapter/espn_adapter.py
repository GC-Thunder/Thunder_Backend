def normalize_match_details(raw_data: dict) -> dict:
    return {
        "id": raw_data.get("object_id"),
        "teams": raw_data.get("teams"),
        "venue": raw_data.get("venue"),
        "status": raw_data.get("status"),
    }






# Normalize scraped data (dict → structured format)

# espn_adapter.py
# def adapt_espn_match(raw_data: dict) -> dict:
#     return {
#         "match_id": raw_data["object_id"],
#         "teams": [raw_data["team1"]["name"], raw_data["team2"]["name"]],
#         ...
#     }

# # sportmonks_adapter.py
# def adapt_sportmonks_match(api_response: dict) -> dict:
#     return {
#         "match_id": api_response["id"],
#         "teams": [
#             api_response["localteam"]["name"],
#             api_response["visitorteam"]["name"]
#         ],
#         ...
#     }



# internal schema {
#   "match_id": str,
#   "series": str,
#   "teams": [str, str],
#   "venue": str,
#   "start_time": datetime,
#   "result": str,
#   "status": str,
#   "scorecard": dict,
# }
