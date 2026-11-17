export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

export interface CandidateSkill {
  id: number;
  name: string;
  category: string;
  proficiency: string;
  years_experience: number;
}

export interface CandidateEducation {
  id: number;
  degree: string;
  field_of_study: string;
  institution: string;
  end_year?: number;
  cgpa_or_percentage?: number;
  is_highest: boolean;
}

export interface CandidateProfile {
  id: number;
  user_id: number;
  headline: string;
  summary?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  total_experience_years: number;
  current_location: string;
  willing_to_relocate: boolean;
  expected_ctc?: number;
  notice_period_days: number;
  user?: User;
  skills?: CandidateSkill[];
  education?: CandidateEducation[];
}

export interface DiscoveredJob {
  id: number;
  job_uid: string;
  title: string;
  company_name: string;
  category: string;
  location: string;
  city: string;
  work_mode: string;
  min_experience: number;
  max_experience?: number;
  description: string;
  official_application_url: string;
  status: string;
  match_score?: number;
}

export interface ApplicationStats {
  total_applications: number;
  awaiting_approval: number;
  submitted: number;
  confirmed: number;
  interviews: number;
  assessments: number;
  offers: number;
  rejections: number;
}

export interface FormPreviewField {
  field_name: string;
  field_label: string;
  field_value: any;
  field_type: string;
  required: boolean;
  source: string;
}

export interface ScreeningQuestionAnswer {
  question: string;
  answer: any;
  source: string;
  is_truthful: boolean;
  needs_review: boolean;
  explanation: string;
}

export interface ApplicationPreview {
  application_id?: number;
  candidate_id: number;
  job_id: number;
  job_title: string;
  company_name: string;
  official_application_url: string;
  resume_id?: number;
  resume_pdf_path?: string;
  resume_docx_path?: string;
  mapped_fields: FormPreviewField[];
  screening_questions: ScreeningQuestionAnswer[];
  candidate_approved: boolean;
  status: string;
  mode: string;
  can_submit: boolean;
  blockers: string[];
}

export interface ApplicationRecord {
  id: number;
  candidate_id: number;
  job_id: number;
  resume_id?: number;
  mode: string;
  status: string;
  candidate_approved: boolean;
  submission_ref_id?: string;
  applied_at?: string;
  job_title?: string;
  company_name?: string;
  location?: string;
  updated_at: string;
}
