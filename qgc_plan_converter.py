
import json
import csv
import uuid

def convert_csv_to_plan(csv_path, output_path="mission.plan"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        waypoints = [row for row in reader]

    if not waypoints or "latitude" not in waypoints[0] or "longitude" not in waypoints[0]:
        raise ValueError("CSV must have 'latitude' and 'longitude' columns")

    mission_items = []
    for i, wp in enumerate(waypoints):
        lat = float(wp["latitude"])
        lon = float(wp["longitude"])
        item = {
            "AMSLAltAboveTerrain": None,
            "Altitude": 10,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 16,
            "doJumpId": i+1,
            "frame": 3,
            "params": [0, 0, 0, None, lat, lon, 10],
            "type": "SimpleItem"
        }
        mission_items.append(item)

    plan_data = {
        "fileType": "Plan",
        "geoFence": {"circles": [], "polygons": [], "version": 2},
        "groundStation": "QGroundControl",
        "mission": {
            "cruiseSpeed": 3,
            "firmwareType": 12,
            "hoverSpeed": 2,
            "items": mission_items,
            "plannedHomePosition": [float(waypoints[0]["latitude"]), float(waypoints[0]["longitude"]), 10],
            "vehicleType": 2,
            "version": 2
        },
        "rallyPoints": {"points": [], "version": 2},
        "version": 1
    }

    with open(output_path, "w") as f:
        json.dump(plan_data, f, indent=4)

    print(f"✅ Converted {csv_path} to QGC plan: {output_path}")
