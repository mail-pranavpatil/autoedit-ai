-- Consolidated initial schema for AutoEdit AI / Eren, replacing Alembic
-- revisions 0001-0006. Fresh-start cutover to Supabase: `users` becomes a
-- profile table keyed off Supabase's own `auth.users`, auto-populated by a
-- trigger on signup, instead of owning its own identity/password columns.
--
-- Timestamp columns intentionally use `timestamp` (no tz), matching the
-- existing SQLAlchemy `DateTime` (naive) columns throughout the app's
-- pipeline code, which compares naive `datetime.utcnow()` values everywhere
-- -- switching to `timestamptz` here would make psycopg2 return
-- timezone-aware datetimes and break those comparisons.

create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  name text,
  picture_url text,
  youtube_auto_upload boolean not null default true,
  onboarding_completed boolean not null default false,
  editing_experience text,
  creation_reason text,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);

-- Auto-create a public.users row whenever Supabase creates an auth.users row.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.users (id, email, name, picture_url)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'name', new.raw_user_meta_data ->> 'full_name'),
    new.raw_user_meta_data ->> 'avatar_url'
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();


create table public.drive_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id),
  provider varchar(32) not null default 'google',
  access_token_encrypted text not null,
  refresh_token_encrypted text,
  token_expiry timestamp,
  scopes text,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);
create index ix_drive_connections_user_id on public.drive_connections(user_id);


create table public.connected_channels (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  platform varchar(32) not null default 'youtube',
  channel_id varchar(255) not null,
  channel_title varchar(255) not null,
  thumbnail_url varchar(1024),
  access_token_encrypted text,
  refresh_token_encrypted text,
  token_expiry timestamp,
  goals jsonb,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);
create index ix_connected_channels_user_id on public.connected_channels(user_id);
create index ix_connected_channels_channel_id on public.connected_channels(channel_id);


create table public.channel_stats_snapshots (
  id uuid primary key default gen_random_uuid(),
  channel_id uuid not null references public.connected_channels(id) on delete cascade,
  views bigint not null,
  subscribers integer not null,
  video_count integer not null,
  captured_at timestamp not null default now()
);
create index ix_channel_stats_snapshots_channel_id on public.channel_stats_snapshots(channel_id);
create index ix_channel_stats_snapshots_channel_captured on public.channel_stats_snapshots(channel_id, captured_at);


create table public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id),
  name varchar(255) not null,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);
create index ix_projects_user_id on public.projects(user_id);


create table public.source_folders (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id),
  provider varchar(32) not null default 'google',
  external_folder_id varchar(255) not null,
  folder_name varchar(512) not null,
  created_at timestamp not null default now()
);
create index ix_source_folders_project_id on public.source_folders(project_id);


create table public.videos (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id),
  external_file_id varchar(255),
  filename varchar(512) not null,
  source_url text,
  local_path text,
  source_hash varchar(64),
  duration double precision,
  width integer,
  height integer,
  fps double precision,
  thumbnail_path text,
  status varchar(32) not null default 'DISCOVERED',
  progress integer not null default 0,
  current_stage varchar(64),
  error_message text,
  failed_stage varchar(64),
  retry_count integer not null default 0,
  celery_task_id varchar(64),
  created_at timestamp not null default now(),
  updated_at timestamp not null default now(),
  constraint uq_project_drive_file unique (project_id, external_file_id)
);
create index ix_videos_project_id on public.videos(project_id);
create index ix_videos_source_hash on public.videos(source_hash);
create index ix_videos_status on public.videos(status);


create table public.transcripts (
  id uuid primary key default gen_random_uuid(),
  video_id uuid not null unique references public.videos(id),
  provider varchar(64) not null,
  language varchar(16),
  full_text text not null,
  segments_json jsonb not null,
  source_hash varchar(64),
  created_at timestamp not null default now()
);
create index ix_transcripts_source_hash on public.transcripts(source_hash);


create table public.edit_plans (
  id uuid primary key default gen_random_uuid(),
  video_id uuid not null references public.videos(id),
  version integer not null default 1,
  plan_json jsonb not null,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);
create index ix_edit_plans_video_id on public.edit_plans(video_id);


create table public.broll_assets (
  id uuid primary key default gen_random_uuid(),
  video_id uuid not null references public.videos(id),
  provider varchar(64) not null,
  external_id varchar(255),
  asset_type varchar(32) not null,
  query varchar(512) not null,
  source_url text,
  local_path text,
  license_info text,
  metadata_json jsonb,
  created_at timestamp not null default now()
);
create index ix_broll_assets_video_id on public.broll_assets(video_id);


create table public.render_jobs (
  id uuid primary key default gen_random_uuid(),
  video_id uuid not null references public.videos(id),
  status varchar(32) not null default 'QUEUED',
  progress integer not null default 0,
  current_stage varchar(64),
  output_path text,
  error_message text,
  started_at timestamp,
  completed_at timestamp,
  created_at timestamp not null default now()
);
create index ix_render_jobs_video_id on public.render_jobs(video_id);


create table public.youtube_uploads (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  video_id uuid not null unique references public.videos(id) on delete cascade,
  status varchar(32) not null default 'PENDING',
  scheduled_at timestamp,
  youtube_video_id varchar(64),
  youtube_url varchar(512),
  title varchar(128),
  error_message text,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now(),
  constraint uq_youtube_user_slot unique (user_id, scheduled_at)
);
create index ix_youtube_uploads_user_id on public.youtube_uploads(user_id);
create index ix_youtube_uploads_status on public.youtube_uploads(status);


create table public.library_assets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id),
  name varchar(255) not null,
  asset_type varchar(32) not null,
  category varchar(64),
  local_path text not null,
  enabled boolean not null default true,
  is_system boolean not null default false,
  created_at timestamp not null default now()
);


create table public.style_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references public.users(id),
  profile_json jsonb not null,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);


create table public.asset_cache (
  id uuid primary key default gen_random_uuid(),
  cache_key varchar(512) not null unique,
  provider varchar(64) not null,
  payload_json jsonb,
  local_path text,
  created_at timestamp not null default now()
);
create index ix_asset_cache_cache_key on public.asset_cache(cache_key);
