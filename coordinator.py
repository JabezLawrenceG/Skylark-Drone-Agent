import pandas as pd
from datetime import datetime

class DroneCoordinator:
    def __init__(self, pilot_df, drone_df, mission_df):
        self.pilots = pilot_df
        self.drones = drone_df
        self.missions = mission_df

    def check_conflicts(self, pilot_id, drone_id, mission_id):
        """
        Detects scheduling, skill, and maintenance conflicts for a manual assignment.
        """
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
        """
        Heuristic scoring engine to match assets to a project.
        Urgent missions get a higher weight for Availability.
        """
        mission = self.missions[self.missions['project_id'] == mission_id].iloc[0]
        is_urgent = mission['priority'].lower() == 'urgent'
        results = {"pilots": [], "drones": []}

        # Match Pilots
        for _, p in self.pilots.iterrows():
            score = 0
            if p['status'] == 'Available': 
                score += 10 if is_urgent else 5
            if p['location'] == mission['location']: 
                score += 10
            results["pilots"].append({"id": p['pilot_id'], "name": p['name'], "score": score})

        # Match Drones
        for _, d in self.drones.iterrows():
            score = 0
            if d['status'] == 'Available': 
                score += 10 if is_urgent else 5
            if d['location'] == mission['location']: 
                score += 10
            results["drones"].append({"id": d['drone_id'], "model": d['model'], "score": score})

        results["pilots"] = sorted(results["pilots"], key=lambda x: x['score'], reverse=True)
        results["drones"] = sorted(results["drones"], key=lambda x: x['score'], reverse=True)
        return results

    def conversational_query(self, query):
        """
        A Keyword-based NLP engine to handle natural language requests.
        Distinguishes between Drone and Pilot intents.
        """
        query = query.lower()
        
        # 1. Handle Drone Queries
        if any(word in query for word in ["drone", "fleet", "model", "uav"]):
            filtered = self.drones
            if "maintenance" in query or "repair" in query:
                filtered = filtered[filtered['status'] == 'Maintenance']
            elif "available" in query or "ready" in query:
                filtered = filtered[filtered['status'] == 'Available']
            
            capabilities = ["lidar", "rgb", "thermal", "mapping"]
            found_cap = [c for c in capabilities if c in query]
            if found_cap:
                filtered = filtered[filtered['capabilities'].str.contains(found_cap[0], case=False)]
            
            return filtered[['drone_id', 'model', 'status', 'capabilities']]

        # 2. Handle Pilot Queries
        else:
            filtered = self.pilots
            
            # Status Intent
            if "leave" in query or "off" in query:
                filtered = filtered[filtered['status'] == 'On Leave']
            elif "available" in query or "free" in query:
                filtered = filtered[filtered['status'] == 'Available']
            elif "assigned" in query or "busy" in query:
                filtered = filtered[filtered['status'] == 'Assigned']

            # Location Intent
            locations = self.pilots['location'].unique()
            found_loc = [loc for loc in locations if loc.lower() in query]
            if found_loc:
                filtered = filtered[filtered['location'].str.contains(found_loc[0], case=False)]

            # Skill/Cert Intent
            skills = ["mapping", "inspection", "thermal", "night ops", "dgca"]
            found_skills = [s for s in skills if s in query]
            if found_skills:
                mask = (filtered['skills'].str.contains(found_skills[0], case=False)) | \
                       (filtered['certifications'].str.contains(found_skills[0], case=False))
                filtered = filtered[mask]

            return filtered[['name', 'location', 'skills', 'status']]
