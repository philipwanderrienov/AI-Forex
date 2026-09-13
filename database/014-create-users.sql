BEGIN;

CREATE TABLE IF NOT EXISTS public.users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username varchar(100) NOT NULL,
    password_hash varchar(512) NOT NULL,
    role varchar(20) NOT NULL DEFAULT 'USER',
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_users_role CHECK (role IN ('USER', 'ADMIN'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username
    ON public.users (username);

COMMIT;

-- Create a password hash with:
-- dotnet run --project src/ForexIntelligence.Api -- --hash-password
--
-- Then insert the first account without supplying an id; PostgreSQL generates it automatically:
-- INSERT INTO public.users
--     (username, password_hash, role, is_active)
-- VALUES
--     ('admin', '<PBKDF2_HASH>', 'ADMIN', true);
