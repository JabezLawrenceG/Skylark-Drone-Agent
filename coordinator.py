import pandas as pd
from datetime import datetime

class DroneCoordinator:
    def __init__(self, pilot_df, drone_df, mission_df):
        self.pilots = pilot_df
        self.drones = drone_df
        self.missions = mission_df

    def check_conflicts(self, pilot_id, drone_id, mission_id):
        conflicts = []
        mission = self.missions[self.missions['project_id'] == mission_id].iloc[0]
        pilot = self.pilots[self.pilots['pilot_id'] == pilot_id].iloc[0]
        drone = self.drones[self.drones['drone_id'] == drone_id].iloc[0]

        # 1. Skill & Certification Check
        req_skills = set([s.strip() for s in mission['required_skills'].split(',')])
        pilot_skills = set([s.strip() for s in pilot['skills'].split(',')])
        if not req_skills.issubset(pilot_skills):
            conflicts.append(f"Skill mismatch: Pilot lacks {req_skills - pilot_skills}")

        req_certs = set([c.strip() for c in mission['required_certs'].split(',')])
        pilot_certs = set([c.strip() for c in pilot['certifications'].split(',')])
        if not req_certs.issubset(pilot_certs):
            conflicts.append(f"Cert mismatch: Pilot lacks {req_certs - pilot_certs}")

        # 2. Status & Maintenance Check
        if drone['status'] == 'Maintenance':
            conflicts.append(f"Drone {drone_id} is currently in Maintenance.")
        if pilot['status'] == 'On Leave':
            conflicts.append(f"Pilot {pilot['name']} is currently On Leave.")

        # 3. Location Check
        if pilot['location'] != mission['location']:
            conflicts.append(f"Location Alert: Pilot is in {pilot['location']}, mission is in {mission['location']}.")
        if drone['location'] != mission['location']:
            conflicts.append(f"Location Alert: Drone is in {drone['location']}, mission is in {mission['location']}.")

        return conflicts

    def find_best_matches(self, mission_id):
        mission = self.missions[self.missions['project_id'] == mission_id].iloc[0]
        results = {"pilots": [], "drones": []}

        # Match Pilots
        for _, p in self.pilots.iterrows():
            score = 0
            if p['status'] == 'Available': score += 5
            if p['location'] == mission['location']: score += 10
            results["pilots"].append({"id": p['pilot_id'], "name": p['name'], "score": score})

        # Match Drones
        for _, d in self.drones.iterrows():
            score = 0
            if d['status'] == 'Available': score += 5
            if d['location'] == mission['location']: score += 10
            results["drones"].append({"id": d['drone_id'], "model": d['model'], "score": score})

        results["pilots"] = sorted(results["pilots"], key=lambda x: x['score'], reverse=True)
        results["drones"] = sorted(results["drones"], key=lambda x: x['score'], reverse=True)
        return results

    # FIX: Indented this function to be part of the class
    def conversational_query(self, query):
        query = query.lower()
        
        # Search for Locations
        locations = self.pilots['location'].unique()
        found_loc = [loc for loc in locations if loc.lower() in query]

        # Search for Skills
        all_skills = ["mapping", "inspection", "thermal", "night ops"]
        found_skills = [skill for skill in all_skills if skill in query]

        # Logic: Filter based on found keywords
        filtered_pilots = self.pilots
        if found_loc:
            filtered_pilots = filtered_pilots[filtered_pilots['location'].str.contains(found_loc[0], case=False)]
        if found_skills:
            filtered_pilots = filtered_pilots[filtered_pilots['skills'].str.contains(found_skills[0], case=False)]

        return filtered_pilots[['name', 'location', 'skills', 'status']]
