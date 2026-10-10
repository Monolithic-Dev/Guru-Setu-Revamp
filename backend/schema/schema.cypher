// GuruSetu graph schema: constraints and indexes (Neo4j 5 Community).
// Single source of truth for labels, keys and indexes. Entity meanings: docs/04-backend/backend.md §2.
// Applied idempotently on API startup and by scripts/seed.py. Community edition has no property-existence
// constraints; required fields and types are enforced by the Pydantic models.

// ENT-01 User
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;
CREATE CONSTRAINT user_email IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE;
CREATE CONSTRAINT student_roll_no IF NOT EXISTS FOR (s:Student) REQUIRE s.roll_no IS UNIQUE;
CREATE CONSTRAINT faculty_employee_id IF NOT EXISTS FOR (f:Faculty) REQUIRE f.employee_id IS UNIQUE;
CREATE INDEX user_dept IF NOT EXISTS FOR (u:User) ON (u.dept_code);

// ENT-02 Department
CREATE CONSTRAINT department_code IF NOT EXISTS FOR (d:Department) REQUIRE d.code IS UNIQUE;

// ENT-03 Concept
CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE;

// ENT-04 Opening
CREATE CONSTRAINT opening_id IF NOT EXISTS FOR (o:Opening) REQUIRE o.id IS UNIQUE;
CREATE INDEX opening_status IF NOT EXISTS FOR (o:Opening) ON (o.status);

// ENT-05 Evidence
CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;
CREATE INDEX evidence_sha256 IF NOT EXISTS FOR (e:Evidence) ON (e.sha256);
CREATE INDEX evidence_status IF NOT EXISTS FOR (e:Evidence) ON (e.status);
CREATE INDEX evidence_cert_id IF NOT EXISTS FOR (e:Evidence) ON (e.certificate_id);

// ENT-06 Issuer
CREATE CONSTRAINT issuer_name IF NOT EXISTS FOR (i:Issuer) REQUIRE i.name IS UNIQUE;

// ENT-07 Term
CREATE CONSTRAINT term_id IF NOT EXISTS FOR (t:Term) REQUIRE t.id IS UNIQUE;

// ENT-08 AcademicRecord [MOCK]
CREATE CONSTRAINT academic_record_id IF NOT EXISTS FOR (a:AcademicRecord) REQUIRE a.id IS UNIQUE;

// ENT-09 Session
CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE;
CREATE INDEX session_date IF NOT EXISTS FOR (s:Session) ON (s.date);

// ENT-10 ActionItem
CREATE CONSTRAINT action_item_id IF NOT EXISTS FOR (a:ActionItem) REQUIRE a.id IS UNIQUE;
CREATE INDEX action_item_status_due IF NOT EXISTS FOR (a:ActionItem) ON (a.status, a.due_date);

// ENT-11 Issue
CREATE CONSTRAINT issue_id IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE;
CREATE INDEX issue_status IF NOT EXISTS FOR (i:Issue) ON (i.status);

// ENT-12 Notification
CREATE CONSTRAINT notification_id IF NOT EXISTS FOR (n:Notification) REQUIRE n.id IS UNIQUE;
CREATE INDEX notification_created IF NOT EXISTS FOR (n:Notification) ON (n.created_at);

// ENT-13 Criterion [MOCK]
CREATE CONSTRAINT criterion_code IF NOT EXISTS FOR (c:Criterion) REQUIRE c.code IS UNIQUE;

// ENT-14 StatusEvent
CREATE CONSTRAINT status_event_id IF NOT EXISTS FOR (e:StatusEvent) REQUIRE e.id IS UNIQUE;
CREATE INDEX status_event_entity IF NOT EXISTS FOR (e:StatusEvent) ON (e.entity_id);

// ENT-15 Counter
CREATE CONSTRAINT counter_key IF NOT EXISTS FOR (c:Counter) REQUIRE (c.name, c.date) IS UNIQUE;

// ENT-21 IdempotencyKey
CREATE CONSTRAINT idempotency_key IF NOT EXISTS FOR (k:IdempotencyKey) REQUIRE (k.key, k.user_id) IS UNIQUE;

// ENT-17 / ENT-18 relationship ids (relationship property indexes, Neo4j 5)
CREATE INDEX mentors_id IF NOT EXISTS FOR ()-[m:MENTORS]-() ON (m.id);
CREATE INDEX applied_to_id IF NOT EXISTS FOR ()-[a:APPLIED_TO]-() ON (a.id);

// MDL-02 vector indexes (384-d, cosine). Dimensions must match EMBEDDING_MODEL (audit H1).
CREATE VECTOR INDEX student_embedding IF NOT EXISTS FOR (s:Student) ON (s.embedding)
  OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX opening_embedding IF NOT EXISTS FOR (o:Opening) ON (o.embedding)
  OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}};
