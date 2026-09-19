import json
from neo4j import GraphDatabase


class Neo4jStore:
    def __init__(self, uri: str, username: str, password: str):
        self.enabled = bool(uri and username and password)
        self.driver = None
        if self.enabled:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        if self.driver:
            self.driver.close()

    def create_constraints(self):
        if not self.driver:
            return
        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT entity_name IF NOT EXISTS "
                "FOR (e:Entity) REQUIRE e.name IS UNIQUE"
            )

    def upsert(self, items: list[dict]):
        if not self.driver:
            return 0

        count = 0
        with self.driver.session() as session:
            for item in items:
                source = item["source"]
                for entity in item.get("entities", []):
                    session.run(
                        """
                        MERGE (e:Entity {name:$name})
                        SET e.source=$source
                        """,
                        name=entity,
                        source=source,
                    )

                for rel in item.get("relationships", []):
                    session.run(
                        """
                        MERGE (a:Entity {name:$source_entity})
                        MERGE (b:Entity {name:$target_entity})
                        MERGE (a)-[r:RELATED_TO {type:$relation}]->(b)
                        SET r.source=$source
                        """,
                        source_entity=rel["source"],
                        target_entity=rel["target"],
                        relation=rel["relation"],
                        source=source,
                    )
                count += len(item.get("entities", [])) + len(item.get("relationships", []))
        return count

    def search(self, terms: list[str], limit: int = 5):
        if not self.driver or not terms:
            return []

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Entity)
                WHERE any(t IN $terms WHERE toLower(a.name) CONTAINS toLower(t))
                OPTIONAL MATCH (a)-[r:RELATED_TO]->(b:Entity)
                RETURN a.name AS entity,
                       collect({
                         relation: r.type,
                         target: b.name
                       })[0..10] AS relations
                LIMIT $limit
                """,
                terms=terms,
                limit=limit,
            )
            return [record.data() for record in result]
