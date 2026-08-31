-- =====================================================================
-- LearnSync AI: Seed Data Script
-- Populates comprehensive mock data for all existing users in auth.users
-- =====================================================================

DO $$
DECLARE
    u RECORD;
    v_profile_id UUID;
    v_course_cs301 UUID;
    v_course_cs340 UUID;
    v_course_bio101 UUID;
    v_folder_consensus UUID;
    v_folder_raft UUID;
    v_folder_nn UUID;
    v_folder_transformers UUID;
    v_doc_raft UUID;
    v_doc_paxos UUID;
    v_doc_attn UUID;
    v_kc_raft_leader UUID;
    v_kc_raft_log UUID;
    v_kc_attn_self UUID;
    v_kc_backprop UUID;
    v_card1 UUID;
    v_card2 UUID;
    v_card3 UUID;
    v_card4 UUID;
    v_zero_vector TEXT;
BEGIN
    -- Construct a valid 1536-dimension mock vector string
    v_zero_vector := '[' || array_to_string(array_fill(0.025, ARRAY[1536]), ',') || ']';

    FOR u IN SELECT id, email, raw_user_meta_data FROM auth.users LOOP
        v_profile_id := u.id;

        -- 1. Profiles
        INSERT INTO public.profiles (id, email, full_name, learning_style, target_retention, onboarding_completed)
        VALUES (
            v_profile_id,
            u.email,
            COALESCE(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name', split_part(u.email, '@', 1)),
            'read_write',
            0.90,
            TRUE
        )
        ON CONFLICT (id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            learning_style = EXCLUDED.learning_style,
            target_retention = EXCLUDED.target_retention,
            onboarding_completed = EXCLUDED.onboarding_completed;

        -- Clean up existing seeded data for idempotency
        DELETE FROM public.courses WHERE user_id = v_profile_id;
        DELETE FROM public.events WHERE user_id = v_profile_id;
        DELETE FROM public.workload_logs WHERE user_id = v_profile_id;
        DELETE FROM public.burnout_triggers WHERE user_id = v_profile_id;

        -- 2. Courses
        INSERT INTO public.courses (id, user_id, name, code, term, color, description)
        VALUES 
            (gen_random_uuid(), v_profile_id, 'Distributed Systems & Consensus', 'CS301', 'Fall 2026', '#3b82f6', 'Study of consensus protocols (Raft, Paxos), fault-tolerance, and distributed storage engines.')
            RETURNING id INTO v_course_cs301;

        INSERT INTO public.courses (id, user_id, name, code, term, color, description)
        VALUES 
            (gen_random_uuid(), v_profile_id, 'Deep Learning & Neural Architectures', 'CS340', 'Fall 2026', '#8b5cf6', 'Exploration of transformer architectures, attention mechanisms, backprop dynamics, and optimization.')
            RETURNING id INTO v_course_cs340;

        INSERT INTO public.courses (id, user_id, name, code, term, color, description)
        VALUES 
            (gen_random_uuid(), v_profile_id, 'Molecular Biology & Genetics', 'BIO101', 'Fall 2026', '#10b981', 'Foundations of cellular respiration, DNA replication, translation, and CRISPR gene regulation.')
            RETURNING id INTO v_course_bio101;

        -- 3. Virtual Folders
        INSERT INTO public.virtual_folders (id, user_id, course_id, parent_id, name, materialized_path, depth)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs301, NULL, 'Module 1: Consensus Protocols', '/consensus', 0)
            RETURNING id INTO v_folder_consensus;

        INSERT INTO public.virtual_folders (id, user_id, course_id, parent_id, name, materialized_path, depth)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs301, v_folder_consensus, 'Raft & Paxos Formalisms', '/consensus/raft-paxos', 1)
            RETURNING id INTO v_folder_raft;

        INSERT INTO public.virtual_folders (id, user_id, course_id, parent_id, name, materialized_path, depth)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs340, NULL, 'Neural Networks & Optimization', '/neural-networks', 0)
            RETURNING id INTO v_folder_nn;

        INSERT INTO public.virtual_folders (id, user_id, course_id, parent_id, name, materialized_path, depth)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs340, NULL, 'Transformers & Attention Mechanisms', '/transformers', 0)
            RETURNING id INTO v_folder_transformers;

        -- 4. Documents
        INSERT INTO public.documents (id, user_id, course_id, folder_id, file_name, storage_path, file_type, file_size_bytes, status)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs301, v_folder_raft, 'Raft_Consensus_Paper.pdf', 'cs301/consensus/raft_paper.pdf', 'application/pdf', 1048576, 'indexed')
            RETURNING id INTO v_doc_raft;

        INSERT INTO public.documents (id, user_id, course_id, folder_id, file_name, storage_path, file_type, file_size_bytes, status)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs301, v_folder_raft, 'Paxos_Made_Moderately_Complex.pdf', 'cs301/consensus/paxos.pdf', 'application/pdf', 845200, 'indexed')
            RETURNING id INTO v_doc_paxos;

        INSERT INTO public.documents (id, user_id, course_id, folder_id, file_name, storage_path, file_type, file_size_bytes, status)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs340, v_folder_transformers, 'Attention_Is_All_You_Need.pdf', 'cs340/transformers/attention.pdf', 'application/pdf', 2145700, 'indexed')
            RETURNING id INTO v_doc_attn;

        -- 5. Document Chunks (500-token blocks with 1536-dim vector embeddings)
        INSERT INTO public.document_chunks (user_id, document_id, folder_id, chunk_index, content, token_count, embedding)
        VALUES 
            (
                v_profile_id, 
                v_doc_raft, 
                v_folder_raft, 
                0, 
                'Raft achieves consensus via an elected leader. A server is always in one of three states: Leader, Follower, or Candidate. Leaders send periodic heartbeats (AppendEntries RPCs with no log entries) to maintain authority.', 
                42, 
                v_zero_vector::vector
            ),
            (
                v_profile_id, 
                v_doc_raft, 
                v_folder_raft, 
                1, 
                'In Raft leader election, if a follower receives no communication over an election timeout, it transitions to candidate, increments its currentTerm, votes for itself, and issues RequestVote RPCs in parallel to all other nodes.', 
                46, 
                v_zero_vector::vector
            ),
            (
                v_profile_id, 
                v_doc_paxos, 
                v_folder_raft, 
                0, 
                'Paxos proceeds in two phases. Phase 1 (Prepare): A proposer chooses a proposal number n and sends a prepare request to a majority of acceptors. Phase 2 (Accept): If accepted by a majority, the proposer issues an accept request.', 
                48, 
                v_zero_vector::vector
            ),
            (
                v_profile_id, 
                v_doc_attn, 
                v_folder_transformers, 
                0, 
                'The Transformer model relies entirely on self-attention mechanisms to compute representations of its input and output without using sequence-aligned RNNs or convolution. Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V.', 
                45, 
                v_zero_vector::vector
            );

        -- 6. Knowledge Components (Curriculum atomic units for BKT)
        INSERT INTO public.knowledge_components (id, user_id, course_id, folder_id, name, description)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs301, v_folder_raft, 'Raft Leader Election', 'Candidate election timeouts, term numbers, and majority voting logic.')
            RETURNING id INTO v_kc_raft_leader;

        INSERT INTO public.knowledge_components (id, user_id, course_id, folder_id, name, description)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs301, v_folder_raft, 'Raft Log Replication & Safety', 'Log consistency invariant, commit index progression, and conflict resolution.')
            RETURNING id INTO v_kc_raft_log;

        INSERT INTO public.knowledge_components (id, user_id, course_id, folder_id, name, description)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs340, v_folder_transformers, 'Scaled Dot-Product Attention', 'Mathematical formulation and gradient flow of query-key-value matrix products.')
            RETURNING id INTO v_kc_attn_self;

        INSERT INTO public.knowledge_components (id, user_id, course_id, folder_id, name, description)
        VALUES 
            (gen_random_uuid(), v_profile_id, v_course_cs340, v_folder_nn, 'Backpropagation & Chain Rule', 'Matrix calculus derivatives and error propagation in multi-layer perceptrons.')
            RETURNING id INTO v_kc_backprop;

        -- 7. Student KC Mastery (Bayesian Knowledge Tracing real-time states)
        INSERT INTO public.student_kc_mastery (user_id, kc_id, p_l, p_transit, p_guess, p_slip, total_attempts, correct_attempts)
        VALUES 
            (v_profile_id, v_kc_raft_leader, 0.88, 0.15, 0.20, 0.08, 14, 12),
            (v_profile_id, v_kc_raft_log, 0.52, 0.15, 0.20, 0.12, 7, 4),
            (v_profile_id, v_kc_attn_self, 0.94, 0.18, 0.15, 0.05, 18, 17),
            (v_profile_id, v_kc_backprop, 0.40, 0.12, 0.25, 0.10, 9, 4);

        -- 8. Flashcards (Spaced Repetition tracking via FSRS)
        INSERT INTO public.flashcards (id, user_id, folder_id, kc_id, front, back, stability, difficulty, reps, lapses, state, is_leech, is_paused, due)
        VALUES 
            (
                gen_random_uuid(), v_profile_id, v_folder_raft, v_kc_raft_leader,
                'What are the 3 valid runtime states for a node in the Raft consensus protocol?',
                'Leader, Follower, and Candidate.',
                7.4, 3.2, 5, 0, 2, FALSE, FALSE, NOW() + INTERVAL '2 days'
            )
            RETURNING id INTO v_card1;

        INSERT INTO public.flashcards (id, user_id, folder_id, kc_id, front, back, stability, difficulty, reps, lapses, state, is_leech, is_paused, due)
        VALUES 
            (
                gen_random_uuid(), v_profile_id, v_folder_raft, v_kc_raft_leader,
                'What quorum size is required for a Raft Candidate to transition to the Leader state?',
                'A strict majority of nodes in the cluster (i.e. floor(N/2) + 1).',
                5.8, 4.0, 4, 1, 2, FALSE, FALSE, NOW() - INTERVAL '1 hour'
            )
            RETURNING id INTO v_card2;

        INSERT INTO public.flashcards (id, user_id, folder_id, kc_id, front, back, stability, difficulty, reps, lapses, state, is_leech, is_paused, due)
        VALUES 
            (
                gen_random_uuid(), v_profile_id, v_folder_transformers, v_kc_attn_self,
                'Write the standard Scaled Dot-Product Attention equation.',
                'Attention(Q, K, V) = softmax((Q * K^T) / sqrt(d_k)) * V',
                12.5, 2.5, 6, 0, 2, FALSE, FALSE, NOW() + INTERVAL '5 days'
            )
            RETURNING id INTO v_card3;

        INSERT INTO public.flashcards (id, user_id, folder_id, kc_id, front, back, stability, difficulty, reps, lapses, state, is_leech, is_paused, due)
        VALUES 
            (
                gen_random_uuid(), v_profile_id, v_folder_raft, v_kc_raft_log,
                'What happens in Paxos Phase 2b when an acceptor receives an Accept(n, v) request?',
                'The acceptor accepts proposal (n, v) if and only if it has not responded to any Prepare(n'') with n'' > n.',
                1.2, 8.5, 8, 4, 3, TRUE, TRUE, NOW() - INTERVAL '1 day'
            )
            RETURNING id INTO v_card4;

        -- 9. Review Logs (Telemetry logs of review ratings)
        INSERT INTO public.review_logs (user_id, flashcard_id, rating, state, elapsed_days, scheduled_days, review_time)
        VALUES 
            (v_profile_id, v_card1, 3, 2, 2.5, 7.4, NOW() - INTERVAL '1 day'),
            (v_profile_id, v_card2, 2, 2, 1.8, 5.8, NOW() - INTERVAL '3 days'),
            (v_profile_id, v_card3, 4, 2, 4.2, 12.5, NOW() - INTERVAL '2 days'),
            (v_profile_id, v_card4, 1, 3, 0.5, 1.2, NOW() - INTERVAL '1 day');

        -- 10. Events (Deadlines & Calendar)
        INSERT INTO public.events (user_id, course_id, title, event_type, start_time, end_time, weight, is_completed, source)
        VALUES 
            (v_profile_id, v_course_cs301, 'CS301 Midterm Exam: Consensus & Storage', 'exam', NOW() + INTERVAL '2 days', NOW() + INTERVAL '2 days 2 hours', 3.5, FALSE, 'syllabus'),
            (v_profile_id, v_course_cs340, 'AI Lab 3: Transformer Encoder Implementation', 'assignment', NOW() + INTERVAL '1 day 18 hours', NOW() + INTERVAL '1 day 23 hours', 2.0, FALSE, 'google_calendar'),
            (v_profile_id, v_course_bio101, 'BIO101 Quiz: Cellular Respiration Pathway', 'quiz', NOW() + INTERVAL '3 days 10 hours', NOW() + INTERVAL '3 days 11 hours', 1.0, FALSE, 'syllabus'),
            (v_profile_id, v_course_cs301, 'CS301 Lecture 14: Paxos vs Raft Tradeoffs', 'lecture', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '1 hour', 0.5, TRUE, 'google_calendar');

        -- 11. Workload Logs (Telemetry for rolling Workload Score W(t))
        INSERT INTO public.workload_logs (user_id, score, mode, lookahead_days, active_event_count, recorded_at)
        VALUES 
            (v_profile_id, 0.78, 'busy', 3, 4, NOW()),
            (v_profile_id, 0.65, 'hysteresis_hold', 3, 3, NOW() - INTERVAL '1 day'),
            (v_profile_id, 0.42, 'free', 3, 2, NOW() - INTERVAL '2 days'),
            (v_profile_id, 0.38, 'free', 3, 1, NOW() - INTERVAL '3 days');

        -- 12. Burnout Triggers (B=MAP 90-second micro-interventions)
        INSERT INTO public.burnout_triggers (user_id, trigger_reason, micro_task_prompt, duration_seconds, is_completed, completed_at)
        VALUES 
            (v_profile_id, 'High 3-day deadline density cluster (CS301 Exam + AI Lab 3)', 'Take a 90-second cognitive reset: 4-7-8 breathing and review 2 high-confidence flashcards.', 90, TRUE, NOW() - INTERVAL '4 hours'),
            (v_profile_id, 'Workload Score W(t) surged past 0.75 threshold', '90-Second Focus Sprint: Recite the 3 states of a Raft node out loud.', 90, FALSE, NULL);

    END LOOP;
END $$;
