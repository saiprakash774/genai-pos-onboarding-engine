import json
import os
import time
from neo4j import GraphDatabase

def seed_graph():
    print("Waiting for Neo4j to be ready...")
    time.sleep(15)  # Wait for neo4j container to fully initialize
    
    URI = "bolt://neo4j:7687"
    AUTH = ("neo4j", "password")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'pos_ontology.json')
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                # Clear existing
                session.run("MATCH (n) DETACH DELETE n")
                
                # Insert data
                for edge in data.get('edges', []):
                    rel = edge.get('relation')
                    if rel == 'Applies_To':
                        mod = edge.get('source').replace('Modifier:', '')
                        cat = edge.get('target').replace('Category:', '')
                        
                        session.run(
                            "MERGE (m:Modifier {name: $mod}) "
                            "MERGE (c:Category {name: $cat}) "
                            "MERGE (m)-[:APPLIES_TO]->(c)",
                            mod=mod, cat=cat
                        )
                print("Neo4j successfully seeded with pos_ontology.json!")
    except Exception as e:
        print(f"Failed to seed Neo4j: {e}")

if __name__ == "__main__":
    seed_graph()
