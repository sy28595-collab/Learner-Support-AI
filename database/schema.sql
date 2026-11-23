PRAGMA foreign_keys = ON;

-- 1. Learners Table

CREATE TABLE IF NOT EXISTS learners (
    learner_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- 2. Support Threads Table

CREATE TABLE IF NOT EXISTS support_threads (
    thread_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,

    thread_status TEXT DEFAULT 'open'
        CHECK(thread_status IN ('open', 'resolved', 'closed')),

    source TEXT DEFAULT 'json_import',
    created_at TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (learner_id)
        REFERENCES learners(learner_id)
);


-- 3. Support Messages Table

CREATE TABLE IF NOT EXISTS support_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,

    sender TEXT NOT NULL
        CHECK(sender IN ('learner', 'agent')),

    message TEXT NOT NULL,
    message_order INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (thread_id)
        REFERENCES support_threads(thread_id),

    UNIQUE(thread_id, message_order)
);


-- 4. Issue Tags Table

CREATE TABLE IF NOT EXISTS issue_tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,

    issue_type TEXT,
    entity_type TEXT,
    entity_value TEXT,

    confidence REAL,
    extraction_source TEXT DEFAULT 'nlp',

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (thread_id)
        REFERENCES support_threads(thread_id)
);


-- 5. Handover Summaries Table

CREATE TABLE IF NOT EXISTS handover_summaries (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,

    version INTEGER NOT NULL DEFAULT 1,

    issue TEXT NOT NULL,
    steps_tried TEXT,
    current_status TEXT,
    unresolved_questions TEXT,
    next_action TEXT,

    provider TEXT,
    model TEXT,
    prompt_version TEXT,

    review_status TEXT DEFAULT 'pending'
        CHECK(review_status IN ('pending', 'approved', 'rejected')),

    reviewed_by TEXT,
    reviewed_at TEXT,
    feedback TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (thread_id)
        REFERENCES support_threads(thread_id),

    UNIQUE(thread_id, version)
);


-- Useful Indexes

CREATE INDEX IF NOT EXISTS idx_threads_learner
ON support_threads(learner_id);

CREATE INDEX IF NOT EXISTS idx_messages_thread
ON support_messages(thread_id);

CREATE INDEX IF NOT EXISTS idx_tags_thread
ON issue_tags(thread_id);

CREATE INDEX IF NOT EXISTS idx_summaries_thread
ON handover_summaries(thread_id);

CREATE INDEX IF NOT EXISTS idx_summaries_review
ON handover_summaries(review_status);
-- Agent Feedback Table
CREATE TABLE IF NOT EXISTS agent_feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    corrected_summary TEXT,
    reviewer TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (summary_id)
        REFERENCES handover_summaries(summary_id)
);

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT,
    summary_id INTEGER,
    action TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id)
        REFERENCES support_threads(thread_id),
    FOREIGN KEY (summary_id)
        REFERENCES handover_summaries(summary_id)
);