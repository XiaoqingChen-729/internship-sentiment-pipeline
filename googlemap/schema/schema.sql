-- Schema: Google Play Sentiment Analysis Pipeline
-- category       id, name
-- app            id, name, app_store_id, category_id
-- ingestion_run  id, app_id, run_at, count, status
-- raw_review     review_id, ingestion_run_id, user_name,
--                content, score, reviewed_at, app_version,
--                thumbs_up_count, reply_content
-- quality_flag   id, review_id, flag_type, reason
-- cleaned_review id, review_id, cleaned_content, language,
--                low_signal, is_duplicate, is_english,
--                cleaned_at

-- 1. CATEGORY
CREATE TABLE category (
    id          SERIAL        PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL UNIQUE
);

-- 2. APP
CREATE TABLE app (
    id            SERIAL        PRIMARY KEY,
    name          VARCHAR(100)  NOT NULL,
    app_store_id  VARCHAR(100)  NOT NULL UNIQUE,
    category_id   INT           NOT NULL,
    FOREIGN KEY (category_id) REFERENCES category(id)
);

-- 3. INGESTION_RUN
CREATE TABLE ingestion_run (
    id          SERIAL       PRIMARY KEY,
    app_id      INT          NOT NULL,
    run_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    count       INT          NOT NULL DEFAULT 0,
    status      VARCHAR(20)  NOT NULL DEFAULT 'success'
                             CHECK (status IN ('success', 'failed', 'partial')),
    FOREIGN KEY (app_id) REFERENCES app(id)
);

-- 4. RAW_REVIEW
CREATE TABLE raw_review (
    review_id        VARCHAR(100)  PRIMARY KEY,
    ingestion_run_id INT           NOT NULL,
    user_name        VARCHAR(200)  NOT NULL,
    content          TEXT,
    score            INT           NOT NULL CHECK (score BETWEEN 1 AND 5),
    reviewed_at      TIMESTAMP     NOT NULL,
    app_version      VARCHAR(50),
    thumbs_up_count  INT           NOT NULL DEFAULT 0,
    reply_content    TEXT,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_run(id)
);

-- 5. QUALITY_FLAG
CREATE TABLE quality_flag (
    id          SERIAL        PRIMARY KEY,
    review_id   VARCHAR(100)  NOT NULL,
    flag_type   VARCHAR(50)   NOT NULL
                              CHECK (flag_type IN ('low_signal', 'duplicate', 'non_english', 'template')),
    reason      TEXT,
    FOREIGN KEY (review_id) REFERENCES raw_review(review_id)
);

-- 6. CLEANED_REVIEW
CREATE TABLE cleaned_review (
    id               SERIAL        PRIMARY KEY,
    review_id        VARCHAR(100)  NOT NULL UNIQUE,
    cleaned_content  TEXT,
    language         VARCHAR(10),
    low_signal       BOOLEAN       NOT NULL DEFAULT FALSE,
    is_duplicate     BOOLEAN       NOT NULL DEFAULT FALSE,
    is_english       BOOLEAN       NOT NULL DEFAULT FALSE,
    cleaned_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES raw_review(review_id)
);
