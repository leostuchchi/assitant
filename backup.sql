--
-- PostgreSQL database dump
--

\restrict 2Pd6cuq6PwHwMoO1YNKWccBRDyitQ6cksF04KDgn0uCbOTzT3bo1VrhjpIfDLUx

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: biorhythms; Type: TABLE; Schema: public; Owner: astra_user
--

CREATE TABLE public.biorhythms (
    telegram_id bigint NOT NULL,
    biorhythm_data jsonb NOT NULL,
    calculation_date date NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.biorhythms OWNER TO astra_user;

--
-- Name: calculation_cache; Type: TABLE; Schema: public; Owner: astra_user
--

CREATE TABLE public.calculation_cache (
    telegram_id bigint NOT NULL,
    target_date date NOT NULL,
    data_type character varying(20) NOT NULL,
    calculation_data jsonb NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    cache_priority integer DEFAULT 1
);


ALTER TABLE public.calculation_cache OWNER TO astra_user;

--
-- Name: daily_calculations; Type: TABLE; Schema: public; Owner: astra_user
--

CREATE TABLE public.daily_calculations (
    telegram_id bigint NOT NULL,
    target_date date NOT NULL,
    biorhythm_data jsonb NOT NULL,
    astro_transits_data jsonb NOT NULL,
    calculation_metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    data_hash character varying(64) NOT NULL,
    calculation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ml_features jsonb,
    basic_insights jsonb,
    columntrend_data jsonb,
    trend_data jsonb,
    risk_factors jsonb,
    opportunities jsonb,
    ml_data_quality integer DEFAULT 0
);


ALTER TABLE public.daily_calculations OWNER TO astra_user;

--
-- Name: ml_models; Type: TABLE; Schema: public; Owner: astra_user
--

CREATE TABLE public.ml_models (
    model_id character varying(50) NOT NULL,
    model_version character varying(20) NOT NULL,
    model_type character varying(30) NOT NULL,
    model_metadata jsonb NOT NULL,
    accuracy_score integer,
    training_date date NOT NULL,
    is_active integer DEFAULT 1,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.ml_models OWNER TO astra_user;

--
-- Name: user_astro_profile; Type: TABLE; Schema: public; Owner: astra_user
--

CREATE TABLE public.user_astro_profile (
    telegram_id bigint NOT NULL,
    natal_chart_data jsonb NOT NULL,
    psyho_matrix_data jsonb NOT NULL,
    dominant_energy character varying(50),
    personality_traits jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ml_features jsonb,
    behavior_patterns jsonb,
    compatibility_profile jsonb
);


ALTER TABLE public.user_astro_profile OWNER TO astra_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: astra_user
--

CREATE TABLE public.users (
    telegram_id bigint NOT NULL,
    birth_date date NOT NULL,
    birth_time time without time zone NOT NULL,
    birth_city character varying(100) NOT NULL,
    profession character varying(100),
    job_position character varying(100),
    current_city character varying(100),
    gender character varying(10),
    request_count integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_segment character varying(50),
    activity_level character varying(20),
    data_quality_score integer DEFAULT 0
);


ALTER TABLE public.users OWNER TO astra_user;

--
-- Data for Name: biorhythms; Type: TABLE DATA; Schema: public; Owner: astra_user
--

COPY public.biorhythms (telegram_id, biorhythm_data, calculation_date, created_at, updated_at) FROM stdin;
5960877187	{"cycles": {"physical": {"phase": "высокая активность", "trend": "падает", "value": 0.6311, "percentage": 81.55, "day_in_cycle": 9}, "emotional": {"phase": "критическая точка", "trend": "падает", "value": -0.7818, "percentage": 10.91, "day_in_cycle": 18}, "intuitive": {"phase": "критическая точка", "trend": "растет", "value": -0.9694, "percentage": 1.53, "day_in_cycle": 30}, "intellectual": {"phase": "критическая точка", "trend": "падает", "value": -0.866, "percentage": 6.7, "day_in_cycle": 22}}, "peak_days": [], "days_lived": 19030, "critical_days": [], "overall_energy": {"value": -0.4165, "percentage": 29.17}, "calculation_date": "2025-11-22"}	2025-11-22	2025-11-21 13:57:33.61958	2025-11-21 13:57:33.61958
5960877187	{"cycles": {"physical": {"phase": "пик энергии", "trend": "падает", "value": 0.817, "percentage": 90.85, "day_in_cycle": 8}, "emotional": {"phase": "низкая активность", "trend": "падает", "value": -0.6235, "percentage": 18.83, "day_in_cycle": 17}, "intuitive": {"phase": "критическая точка", "trend": "стабильно", "value": -0.9966, "percentage": 0.17, "day_in_cycle": 29}, "intellectual": {"phase": "критическая точка", "trend": "падает", "value": -0.7557, "percentage": 12.21, "day_in_cycle": 21}}, "peak_days": [{"date": "2025-11-21", "cycles": ["физический"]}], "days_lived": 19029, "critical_days": [], "overall_energy": {"value": -0.299, "percentage": 35.05}, "calculation_date": "2025-11-21"}	2025-11-21	2025-11-21 13:57:49.574865	2025-11-21 13:57:49.574865
5960877187	{"cycles": {"physical": {"phase": "нейтральная фаза", "trend": "падает", "value": 0.1362, "percentage": 56.81, "day_in_cycle": 11}, "emotional": {"phase": "критическая точка", "trend": "падает", "value": -0.9749, "percentage": 1.25, "day_in_cycle": 20}, "intuitive": {"phase": "критическая точка", "trend": "растет", "value": -0.8372, "percentage": 8.14, "day_in_cycle": 32}, "intellectual": {"phase": "критическая точка", "trend": "падает", "value": -0.9898, "percentage": 0.51, "day_in_cycle": 24}}, "peak_days": [], "days_lived": 19032, "critical_days": [{"date": "2025-11-24", "cycles": ["эмоциональный", "интеллектуальный"]}], "overall_energy": {"value": -0.6178, "percentage": 19.11}, "calculation_date": "2025-11-24"}	2025-11-24	2025-11-24 20:08:06.41495	2025-11-24 20:08:06.41495
5960877187	{"cycles": {"physical": {"phase": "нейтральная фаза", "trend": "падает", "value": -0.1362, "percentage": 43.19, "day_in_cycle": 12}, "emotional": {"phase": "критическая точка", "trend": "стабильно", "value": -1.0, "percentage": 0.0, "day_in_cycle": 21}, "intuitive": {"phase": "критическая точка", "trend": "растет", "value": -0.7357, "percentage": 13.21, "day_in_cycle": 33}, "intellectual": {"phase": "критическая точка", "trend": "стабильно", "value": -0.9989, "percentage": 0.06, "day_in_cycle": 25}}, "peak_days": [], "days_lived": 19033, "critical_days": [{"date": "2025-11-25", "cycles": ["эмоциональный", "интеллектуальный"]}], "overall_energy": {"value": -0.6877, "percentage": 15.61}, "calculation_date": "2025-11-25"}	2025-11-25	2025-11-25 11:14:22.473432	2025-11-25 11:14:22.473432
5960877187	{"cycles": {"physical": {"phase": "низкая активность", "trend": "падает", "value": -0.3984, "percentage": 30.08, "day_in_cycle": 13}, "emotional": {"phase": "критическая точка", "trend": "растет", "value": -0.9749, "percentage": 1.25, "day_in_cycle": 22}, "intuitive": {"phase": "низкая активность", "trend": "растет", "value": -0.6142, "percentage": 19.29, "day_in_cycle": 34}, "intellectual": {"phase": "критическая точка", "trend": "растет", "value": -0.9718, "percentage": 1.41, "day_in_cycle": 26}}, "peak_days": [], "days_lived": 19034, "critical_days": [{"date": "2025-11-26", "cycles": ["эмоциональный", "интеллектуальный"]}], "overall_energy": {"value": -0.729, "percentage": 13.55}, "calculation_date": "2025-11-26"}	2025-11-26	2025-11-25 12:06:23.883444	2025-11-25 12:06:23.883444
\.


--
-- Data for Name: calculation_cache; Type: TABLE DATA; Schema: public; Owner: astra_user
--

COPY public.calculation_cache (telegram_id, target_date, data_type, calculation_data, expires_at, created_at, cache_priority) FROM stdin;
\.


--
-- Data for Name: daily_calculations; Type: TABLE DATA; Schema: public; Owner: astra_user
--

COPY public.daily_calculations (telegram_id, target_date, biorhythm_data, astro_transits_data, calculation_metadata, data_hash, calculation_timestamp, ml_features, basic_insights, columntrend_data, trend_data, risk_factors, opportunities, ml_data_quality) FROM stdin;
5960877187	2025-11-25	{"cycles": {"physical": {"phase": "нейтральная фаза", "trend": "падает", "value": -0.1362, "percentage": 43.19, "day_in_cycle": 12}, "emotional": {"phase": "критическая точка", "trend": "стабильно", "value": -1.0, "percentage": 0.0, "day_in_cycle": 21}, "intuitive": {"phase": "критическая точка", "trend": "растет", "value": -0.7357, "percentage": 13.21, "day_in_cycle": 33}, "intellectual": {"phase": "критическая точка", "trend": "стабильно", "value": -0.9989, "percentage": 0.06, "day_in_cycle": 25}}, "days_lived": 19033, "overall_energy": {"value": -0.6877, "percentage": 15.61}, "peak_days_count": 0, "critical_days_count": 1}	{"key_aspects": [{"orb": 0.66, "aspect": "sextile", "strength": 0.89, "is_strong": true, "exact_angle": 60, "actual_angle": 59.34, "natal_planet": "Jupiter", "transit_planet": "Sun"}, {"orb": 1.02, "aspect": "conjunction", "strength": 0.87, "is_strong": true, "exact_angle": 0, "actual_angle": 1.02, "natal_planet": "Jupiter", "transit_planet": "Pluto"}, {"orb": 1.44, "aspect": "square", "strength": 0.82, "is_strong": true, "exact_angle": 90, "actual_angle": 88.56, "natal_planet": "Uranus", "transit_planet": "Jupiter"}, {"orb": 1.91, "aspect": "conjunction", "strength": 0.76, "is_strong": true, "exact_angle": 0, "actual_angle": 1.91, "natal_planet": "Jupiter", "transit_planet": "Moon"}, {"orb": 1.53, "aspect": "sextile", "strength": 0.75, "is_strong": true, "exact_angle": 60, "actual_angle": 58.47, "natal_planet": "Pluto", "transit_planet": "Sun"}], "aspects_count": 28, "error_message": null, "transits_count": 10, "calculation_error": false, "retrograde_planets": [], "strong_aspects_count": 7}	{"data_sources": ["astrology", "biorhythms"], "data_version": "2.0", "calculation_methods": ["swiss_ephemeris", "sine_wave_analysis"], "calculation_timestamp": "2025-11-25T11:14:22.515052"}	1bc146cddfa5010bd5258d6c019926988875e630c7042f6bf5d2c3575923570e	2025-11-25 11:14:22.549806	{"is_weekend": 0.0, "daily_score": 0.39683, "is_peak_day": 0.0, "year_progress": 0.9010989010989011, "astro_activity": 1.0, "energy_overall": 0.1561, "month_progress": 0.8064516129032258, "energy_physical": 0.43189999999999995, "is_critical_day": 0.0, "seasonal_effect": 0.95, "wellbeing_index": 0.32957000000000003, "aspect_intensity": 0.7, "astro_complexity": 1.0, "energy_emotional": 0.0, "energy_stability": 0.5930833227524064, "harmonic_balance": 0.5, "retrograde_impact": 0.0, "adaptability_index": 0.6872333291009626, "day_of_week_effect": 1.05, "productivity_index": 0.36762000000000006, "energy_intellectual": 0.0006}	["🔄 **Энергия на низком уровне** - рекомендуется бережный режим и отдых", "📝 **Лучше сосредоточиться на рутине** - сложные задачи могут требовать больше усилий"]	\N	{"patterns": {}, "statistics": {}, "data_points": 0, "predictions": {"message": "Insufficient data", "confidence": 0.0}, "analysis_date": "2025-11-25T11:14:22.544363", "energy_trends": {"strength": 0.0, "direction": "stable", "max_energy": 100, "min_energy": 0, "volatility": 0.0, "energy_change": 0, "average_energy": 50, "current_energy": 50, "trend_duration": "unknown", "stability_score": 0.5}, "analysis_period": "0 days", "recommendations": ["📊 Соберите больше данных для анализа трендов"]}	["Низкий уровень энергии", "Множество напряженных аспектов"]	["Благоприятные астрологические аспекты"]	90
5960877187	2025-11-24	{"cycles": {"physical": {"phase": "нейтральная фаза", "trend": "падает", "value": 0.1362, "percentage": 56.81, "day_in_cycle": 11}, "emotional": {"phase": "критическая точка", "trend": "падает", "value": -0.9749, "percentage": 1.25, "day_in_cycle": 20}, "intuitive": {"phase": "критическая точка", "trend": "растет", "value": -0.8372, "percentage": 8.14, "day_in_cycle": 32}, "intellectual": {"phase": "критическая точка", "trend": "падает", "value": -0.9898, "percentage": 0.51, "day_in_cycle": 24}}, "days_lived": 19032, "overall_energy": {"value": -0.6178, "percentage": 19.11}, "peak_days_count": 0, "critical_days_count": 1}	{"key_aspects": [{"orb": 0.35, "aspect": "sextile", "strength": 0.94, "is_strong": true, "exact_angle": 60, "actual_angle": 60.35, "natal_planet": "Jupiter", "transit_planet": "Sun"}, {"orb": 1.04, "aspect": "conjunction", "strength": 0.87, "is_strong": true, "exact_angle": 0, "actual_angle": 1.04, "natal_planet": "Jupiter", "transit_planet": "Pluto"}, {"orb": 1.48, "aspect": "square", "strength": 0.81, "is_strong": true, "exact_angle": 90, "actual_angle": 88.52, "natal_planet": "Uranus", "transit_planet": "Jupiter"}, {"orb": 1.44, "aspect": "sextile", "strength": 0.76, "is_strong": true, "exact_angle": 60, "actual_angle": 61.44, "natal_planet": "Mercury", "transit_planet": "Moon"}, {"orb": 2.03, "aspect": "square", "strength": 0.75, "is_strong": true, "exact_angle": 90, "actual_angle": 87.97, "natal_planet": "Sun", "transit_planet": "Jupiter"}], "aspects_count": 26, "error_message": null, "transits_count": 10, "calculation_error": false, "retrograde_planets": [], "strong_aspects_count": 5}	{"data_sources": ["astrology", "biorhythms"], "data_version": "2.0", "calculation_methods": ["swiss_ephemeris", "sine_wave_analysis"], "calculation_timestamp": "2025-11-24T22:08:06.449852"}	cbc6162adf9af23857ee2590ab05250594daddc9a7edf4dc3bc5b5bf495548ee	2025-11-24 22:08:06.491192	{"is_weekend": 0.0, "daily_score": 0.40732999999999997, "is_peak_day": 0.0, "year_progress": 0.8983516483516484, "astro_activity": 1.0, "energy_overall": 0.1911, "month_progress": 0.7741935483870968, "energy_physical": 0.5681, "is_critical_day": 0.0, "seasonal_effect": 0.95, "wellbeing_index": 0.37668, "aspect_intensity": 0.5, "astro_complexity": 1.0, "energy_emotional": 0.0125, "energy_stability": 0.4726522884387485, "harmonic_balance": 0.5, "retrograde_impact": 0.0, "adaptability_index": 0.6390609153754994, "day_of_week_effect": 0.9, "productivity_index": 0.35297, "energy_intellectual": 0.0051}	["🔄 **Энергия на низком уровне** - рекомендуется бережный режим и отдых", "📝 **Лучше сосредоточиться на рутине** - сложные задачи могут требовать больше усилий"]	\N	{"patterns": {}, "statistics": {}, "data_points": 0, "predictions": {"message": "Insufficient data", "confidence": 0.0}, "analysis_date": "2025-11-24T22:08:06.482364", "energy_trends": {"strength": 0.0, "direction": "stable", "max_energy": 100, "min_energy": 0, "volatility": 0.0, "energy_change": 0, "average_energy": 50, "current_energy": 50, "trend_duration": "unknown", "stability_score": 0.5}, "analysis_period": "0 days", "recommendations": ["📊 Соберите больше данных для анализа трендов"]}	["Низкий уровень энергии", "Множество напряженных аспектов"]	["Благоприятные астрологические аспекты"]	90
5960877187	2025-11-26	{"cycles": {"physical": {"phase": "низкая активность", "trend": "падает", "value": -0.3984, "percentage": 30.08, "day_in_cycle": 13}, "emotional": {"phase": "критическая точка", "trend": "растет", "value": -0.9749, "percentage": 1.25, "day_in_cycle": 22}, "intuitive": {"phase": "низкая активность", "trend": "растет", "value": -0.6142, "percentage": 19.29, "day_in_cycle": 34}, "intellectual": {"phase": "критическая точка", "trend": "растет", "value": -0.9718, "percentage": 1.41, "day_in_cycle": 26}}, "days_lived": 19034, "overall_energy": {"value": -0.729, "percentage": 13.55}, "peak_days_count": 0, "critical_days_count": 1}	{"key_aspects": [{"orb": 0.51, "aspect": "sextile", "strength": 0.91, "is_strong": true, "exact_angle": 60, "actual_angle": 59.49, "natal_planet": "Pluto", "transit_planet": "Sun"}, {"orb": 1.0, "aspect": "conjunction", "strength": 0.88, "is_strong": true, "exact_angle": 0, "actual_angle": 1.0, "natal_planet": "Jupiter", "transit_planet": "Pluto"}, {"orb": 1.14, "aspect": "conjunction", "strength": 0.86, "is_strong": true, "exact_angle": 0, "actual_angle": 1.14, "natal_planet": "Neptune", "transit_planet": "Sun"}, {"orb": 1.39, "aspect": "square", "strength": 0.83, "is_strong": true, "exact_angle": 90, "actual_angle": 88.61, "natal_planet": "Uranus", "transit_planet": "Jupiter"}, {"orb": 1.94, "aspect": "square", "strength": 0.76, "is_strong": true, "exact_angle": 90, "actual_angle": 88.06, "natal_planet": "Sun", "transit_planet": "Jupiter"}], "aspects_count": 25, "error_message": null, "transits_count": 10, "calculation_error": false, "retrograde_planets": [], "strong_aspects_count": 6}	{"data_sources": ["astrology", "biorhythms"], "data_version": "2.0", "calculation_methods": ["swiss_ephemeris", "sine_wave_analysis"], "calculation_timestamp": "2025-11-25T14:06:23.920118"}	d02195785af4cd7b4e0031bb74917e665688f8de4b1a231123c54b884182382c	2025-11-25 14:06:23.966015	{"is_weekend": 0.0, "daily_score": 0.39064999999999994, "is_peak_day": 0.0, "year_progress": 0.9038461538461539, "astro_activity": 1.0, "energy_overall": 0.1355, "month_progress": 0.8387096774193549, "energy_physical": 0.30079999999999996, "is_critical_day": 0.0, "seasonal_effect": 0.95, "wellbeing_index": 0.29649000000000003, "aspect_intensity": 0.6, "astro_complexity": 1.0, "energy_emotional": 0.0125, "energy_stability": 0.7289392524010736, "harmonic_balance": 0.5, "retrograde_impact": 0.0, "adaptability_index": 0.7415757009604295, "day_of_week_effect": 1.1, "productivity_index": 0.37343000000000004, "energy_intellectual": 0.0141}	["🔄 **Энергия на низком уровне** - рекомендуется бережный режим и отдых", "📝 **Лучше сосредоточиться на рутине** - сложные задачи могут требовать больше усилий"]	\N	{"patterns": {}, "statistics": {}, "data_points": 0, "predictions": {"message": "Insufficient data", "confidence": 0.0}, "analysis_date": "2025-11-25T14:06:23.957483", "energy_trends": {"strength": 0.0, "direction": "stable", "max_energy": 100, "min_energy": 0, "volatility": 0.0, "energy_change": 0, "average_energy": 50, "current_energy": 50, "trend_duration": "unknown", "stability_score": 0.5}, "analysis_period": "0 days", "recommendations": ["📊 Соберите больше данных для анализа трендов"]}	["Низкий уровень энергии", "Множество напряженных аспектов"]	["Стандартные возможности дня"]	90
5960877187	2025-11-21	{"cycles": {"physical": {"phase": "пик энергии", "trend": "падает", "value": 0.817, "percentage": 90.85, "day_in_cycle": 8}, "emotional": {"phase": "низкая активность", "trend": "падает", "value": -0.6235, "percentage": 18.83, "day_in_cycle": 17}, "intuitive": {"phase": "критическая точка", "trend": "стабильно", "value": -0.9966, "percentage": 0.17, "day_in_cycle": 29}, "intellectual": {"phase": "критическая точка", "trend": "падает", "value": -0.7557, "percentage": 12.21, "day_in_cycle": 21}}, "days_lived": 19029, "overall_energy": {"value": -0.299, "percentage": 35.05}, "peak_days_count": 1, "critical_days_count": 0}	{"key_aspects": [{"orb": 1.04, "aspect": "conjunction", "strength": 0.87, "is_strong": true, "exact_angle": 0, "actual_angle": 1.04, "natal_planet": "Mercury", "transit_planet": "Venus"}, {"orb": 1.09, "aspect": "conjunction", "strength": 0.86, "is_strong": true, "exact_angle": 0, "actual_angle": 1.09, "natal_planet": "Jupiter", "transit_planet": "Pluto"}, {"orb": 1.6, "aspect": "square", "strength": 0.8, "is_strong": true, "exact_angle": 90, "actual_angle": 88.4, "natal_planet": "Uranus", "transit_planet": "Jupiter"}, {"orb": 2.14, "aspect": "square", "strength": 0.73, "is_strong": true, "exact_angle": 90, "actual_angle": 87.86, "natal_planet": "Sun", "transit_planet": "Jupiter"}, {"orb": 2.52, "aspect": "conjunction", "strength": 0.68, "is_strong": false, "exact_angle": 0, "actual_angle": 2.52, "natal_planet": "Ascendant", "transit_planet": "Mars"}], "aspects_count": 26, "error_message": null, "transits_count": 10, "calculation_error": false, "retrograde_planets": [], "strong_aspects_count": 4}	{"data_sources": ["astrology", "biorhythms"], "data_version": "2.0", "calculation_methods": ["swiss_ephemeris", "sine_wave_analysis"], "calculation_timestamp": "2025-11-21T15:57:49.592286"}	14673a328332bf713b666491de226f3d6c24c2aa2c655032b95ea78cff5f744f	2025-11-21 15:57:49.599162	\N	\N	\N	\N	["Множество напряженных аспектов"]	["Стандартные возможности дня"]	10
5960877187	2025-11-22	{"cycles": {"physical": {"phase": "высокая активность", "trend": "падает", "value": 0.6311, "percentage": 81.55, "day_in_cycle": 9}, "emotional": {"phase": "критическая точка", "trend": "падает", "value": -0.7818, "percentage": 10.91, "day_in_cycle": 18}, "intuitive": {"phase": "критическая точка", "trend": "растет", "value": -0.9694, "percentage": 1.53, "day_in_cycle": 30}, "intellectual": {"phase": "критическая точка", "trend": "падает", "value": -0.866, "percentage": 6.7, "day_in_cycle": 22}}, "days_lived": 19030, "overall_energy": {"value": -0.4165, "percentage": 29.17}, "peak_days_count": 0, "critical_days_count": 0}	{"key_aspects": [{"orb": 1.07, "aspect": "conjunction", "strength": 0.87, "is_strong": true, "exact_angle": 0, "actual_angle": 1.07, "natal_planet": "Jupiter", "transit_planet": "Pluto"}, {"orb": 1.18, "aspect": "sextile", "strength": 0.8, "is_strong": true, "exact_angle": 60, "actual_angle": 61.18, "natal_planet": "Uranus", "transit_planet": "Moon"}, {"orb": 1.56, "aspect": "square", "strength": 0.8, "is_strong": true, "exact_angle": 90, "actual_angle": 88.44, "natal_planet": "Uranus", "transit_planet": "Jupiter"}, {"orb": 2.11, "aspect": "square", "strength": 0.74, "is_strong": true, "exact_angle": 90, "actual_angle": 87.89, "natal_planet": "Sun", "transit_planet": "Jupiter"}, {"orb": 1.73, "aspect": "sextile", "strength": 0.71, "is_strong": true, "exact_angle": 60, "actual_angle": 61.73, "natal_planet": "Sun", "transit_planet": "Moon"}], "aspects_count": 25, "error_message": null, "transits_count": 10, "calculation_error": false, "retrograde_planets": [], "strong_aspects_count": 6}	{"data_sources": ["astrology", "biorhythms"], "data_version": "2.0", "calculation_methods": ["swiss_ephemeris", "sine_wave_analysis"], "calculation_timestamp": "2025-11-21T15:57:33.650392"}	f530cef84a4d620c208c396417526f1e6818afc7752b3e43beb1e3c727ad1e57	2025-11-21 15:57:33.660905	\N	\N	\N	\N	["Низкий уровень энергии", "Множество напряженных аспектов"]	["Благоприятные астрологические аспекты"]	10
\.


--
-- Data for Name: ml_models; Type: TABLE DATA; Schema: public; Owner: astra_user
--

COPY public.ml_models (model_id, model_version, model_type, model_metadata, accuracy_score, training_date, is_active, created_at, updated_at) FROM stdin;
feature_engineering	1.0	feature_engineering	{"description": "Basic feature engineering model"}	85	2025-11-25	1	2025-11-25 09:45:37.525788	2025-11-25 09:45:37.525788
trend_analyzer	1.0	trend_analysis	{"description": "Basic trend analysis model"}	80	2025-11-25	1	2025-11-25 09:45:37.525788	2025-11-25 09:45:37.525788
\.


--
-- Data for Name: user_astro_profile; Type: TABLE DATA; Schema: public; Owner: astra_user
--

COPY public.user_astro_profile (telegram_id, natal_chart_data, psyho_matrix_data, dominant_energy, personality_traits, created_at, updated_at, ml_features, behavior_patterns, compatibility_profile) FROM stdin;
5960877187	{"angles": {"ascendant": {"sign": "Sagittarius", "longitude": 249.768107, "sign_index": 8}, "midheaven": {"sign": "Libra", "longitude": 195.579017, "sign_index": 6}}, "houses": {"1": {"sign": "Sagittarius", "sign_index": 8, "cusp_longitude": 249.768107, "position_in_sign": 9.7681}, "2": {"sign": "Capricorn", "sign_index": 9, "cusp_longitude": 288.278236, "position_in_sign": 18.2782}, "3": {"sign": "Pisces", "sign_index": 11, "cusp_longitude": 338.567154, "position_in_sign": 8.5672}, "4": {"sign": "Aries", "sign_index": 0, "cusp_longitude": 15.579017, "position_in_sign": 15.579}, "5": {"sign": "Taurus", "sign_index": 1, "cusp_longitude": 39.255213, "position_in_sign": 9.2552}, "6": {"sign": "Taurus", "sign_index": 1, "cusp_longitude": 56.064133, "position_in_sign": 26.0641}, "7": {"sign": "Gemini", "sign_index": 2, "cusp_longitude": 69.768107, "position_in_sign": 9.7681}, "8": {"sign": "Cancer", "sign_index": 3, "cusp_longitude": 108.278236, "position_in_sign": 18.2782}, "9": {"sign": "Virgo", "sign_index": 5, "cusp_longitude": 158.567154, "position_in_sign": 8.5672}, "10": {"sign": "Libra", "sign_index": 6, "cusp_longitude": 195.579017, "position_in_sign": 15.579}, "11": {"sign": "Scorpio", "sign_index": 7, "cusp_longitude": 219.255213, "position_in_sign": 9.2552}, "12": {"sign": "Scorpio", "sign_index": 7, "cusp_longitude": 236.064133, "position_in_sign": 26.0641}}, "aspects": [{"orb": 0.2442, "aspect": "square", "point1": "Saturn", "point2": "Pluto", "strength": 0.969478500000001, "exact_angle": 90, "actual_angle": 90.2442}, {"orb": 0.253, "aspect": "sextile", "point1": "Mars", "point2": "Saturn", "strength": 0.9578301666666675, "exact_angle": 60, "actual_angle": 60.253}, {"orb": 0.5498, "aspect": "conjunction", "point1": "Sun", "point2": "Uranus", "strength": 0.9312690000000003, "exact_angle": 0, "actual_angle": 0.5498}, {"orb": 0.6237, "aspect": "sextile", "point1": "Neptune", "point2": "Pluto", "strength": 0.8960469999999958, "exact_angle": 60, "actual_angle": 60.6237}, {"orb": 1.6927, "aspect": "square", "point1": "Mars", "point2": "Jupiter", "strength": 0.7884068749999997, "exact_angle": 90, "actual_angle": 91.6927}, {"orb": 1.848, "aspect": "conjunction", "point1": "Venus", "point2": "Ascendant", "strength": 0.7689966250000033, "exact_angle": 0, "actual_angle": 1.848}, {"orb": 2.1899, "aspect": "trine", "point1": "Jupiter", "point2": "Pluto", "strength": 0.7262580000000014, "exact_angle": 120, "actual_angle": 117.8101}, {"orb": 2.2994, "aspect": "conjunction", "point1": "Venus", "point2": "Neptune", "strength": 0.7125811249999998, "exact_angle": 0, "actual_angle": 2.2994}, {"orb": 3.314, "aspect": "trine", "point1": "Moon", "point2": "Midheaven", "strength": 0.58574825, "exact_angle": 120, "actual_angle": 116.686}, {"orb": 3.5326, "aspect": "trine", "point1": "Mars", "point2": "North_Node", "strength": 0.558424875, "exact_angle": 120, "actual_angle": 123.5326}, {"orb": 2.8137, "aspect": "sextile", "point1": "Jupiter", "point2": "Neptune", "strength": 0.5310576666666644, "exact_angle": 60, "actual_angle": 57.1863}, {"orb": 3.7856, "aspect": "opposition", "point1": "Saturn", "point2": "North_Node", "strength": 0.5267975000000007, "exact_angle": 180, "actual_angle": 176.2144}, {"orb": 2.9231, "aspect": "sextile", "point1": "Venus", "point2": "Pluto", "strength": 0.512821833333329, "exact_angle": 60, "actual_angle": 62.9231}, {"orb": 3.9538, "aspect": "trine", "point1": "Sun", "point2": "Moon", "strength": 0.5057752499999975, "exact_angle": 120, "actual_angle": 123.9538}, {"orb": 4.0298, "aspect": "square", "point1": "Pluto", "point2": "North_Node", "strength": 0.4962760000000017, "exact_angle": 90, "actual_angle": 85.9702}, {"orb": 4.1474, "aspect": "conjunction", "point1": "Neptune", "point2": "Ascendant", "strength": 0.48157775000000314, "exact_angle": 0, "actual_angle": 4.1474}, {"orb": 4.5036, "aspect": "trine", "point1": "Moon", "point2": "Uranus", "strength": 0.4370442499999978, "exact_angle": 120, "actual_angle": 124.5036}, {"orb": 4.7711, "aspect": "sextile", "point1": "Pluto", "point2": "Ascendant", "strength": 0.2048173333333333, "exact_angle": 60, "actual_angle": 64.7711}, {"orb": 5.113, "aspect": "sextile", "point1": "Venus", "point2": "Jupiter", "strength": 0.14783249999999748, "exact_angle": 60, "actual_angle": 54.887}, {"orb": 7.2678, "aspect": "conjunction", "point1": "Sun", "point2": "Midheaven", "strength": 0.09152349999999743, "exact_angle": 0, "actual_angle": 7.2678}, {"orb": 5.8109, "aspect": "sextile", "point1": "Ascendant", "point2": "Midheaven", "strength": 0.03151499999999885, "exact_angle": 60, "actual_angle": 54.1891}, {"orb": 7.8177, "aspect": "conjunction", "point1": "Uranus", "point2": "Midheaven", "strength": 0.022792499999997773, "exact_angle": 0, "actual_angle": 7.8177}], "planets": {"Sun": {"sign": "Libra", "speed": 0.991783, "longitude": 202.846829, "retrograde": false, "sign_index": 6, "position_in_sign": 22.8468}, "Mars": {"sign": "Taurus", "speed": -0.319318, "longitude": 34.49982, "retrograde": true, "sign_index": 1, "position_in_sign": 4.4998}, "Moon": {"sign": "Gemini", "speed": 14.301847, "longitude": 78.893031, "retrograde": false, "sign_index": 2, "position_in_sign": 18.893}, "Pluto": {"sign": "Libra", "speed": 0.036903, "longitude": 184.997011, "retrograde": false, "sign_index": 6, "position_in_sign": 4.997}, "Venus": {"sign": "Sagittarius", "speed": 1.118853, "longitude": 247.92008, "retrograde": false, "sign_index": 8, "position_in_sign": 7.9201}, "Saturn": {"sign": "Cancer", "speed": 0.001634, "longitude": 94.752839, "retrograde": false, "sign_index": 3, "position_in_sign": 4.7528}, "Uranus": {"sign": "Libra", "speed": 0.06305, "longitude": 203.396677, "retrograde": false, "sign_index": 6, "position_in_sign": 23.3967}, "Jupiter": {"sign": "Aquarius", "speed": 0.057479, "longitude": 302.807075, "retrograde": false, "sign_index": 10, "position_in_sign": 2.8071}, "Mercury": {"sign": "Scorpio", "speed": 1.092528, "longitude": 227.219508, "retrograde": false, "sign_index": 7, "position_in_sign": 17.2195}, "Neptune": {"sign": "Sagittarius", "speed": 0.02949, "longitude": 245.620729, "retrograde": false, "sign_index": 8, "position_in_sign": 5.6207}, "North_Node": {"sign": "Capricorn", "speed": -0.022226, "longitude": 270.967219, "retrograde": true, "sign_index": 9, "position_in_sign": 0.9672}}, "metadata": {"datetime": {"jd": 2441971.866667, "utc": "1973-10-16T08:48:00+00:00", "local": "1973-10-16T11:48:00+03:00"}, "location": {"lat": 55.7558, "lon": 37.6173, "city": "калининград", "elevation": 156}, "calculation": {"ephemeris": "DE441", "house_system": "Placidus"}}, "placements": {"Sun": 10, "Mars": 4, "Moon": 7, "Pluto": 9, "Venus": 12, "Saturn": 7, "Uranus": 10, "Jupiter": 2, "Mercury": 11, "Neptune": 12, "North_Node": 1}, "ml_features": {"aspect_patterns": {"trines": 0, "squares": 0, "sextiles": 0, "oppositions": 0, "conjunctions": 0}, "element_balance": {"air": 5, "fire": 2, "earth": 2, "water": 2}, "sign_distribution": {"Leo": 0, "Aries": 0, "Libra": 3, "Virgo": 0, "Cancer": 1, "Gemini": 1, "Pisces": 0, "Taurus": 1, "Scorpio": 1, "Aquarius": 1, "Capricorn": 1, "Sagittarius": 2}}}	{"digit_counts": {"total_digits": 7, "strong_digits": ["1"], "missing_digits": ["2", "4", "5", "8"]}, "basic_numbers": {"first": 28, "third": 26, "fourth": 8, "second": 10}, "calculated_at": "2025-11-21T13:25:23.657040", "pythagoras_matrix": {"1": 3, "2": 0, "3": 1, "4": 0, "5": 0, "6": 1, "7": 1, "8": 0, "9": 1}}	интеллектуальная	[]	2025-11-21 13:25:23.634665	2025-11-25 10:22:37.218422	{"generated_at": "2025-11-25T12:22:37.243614", "matrix_energy": "medium", "element_balance": {"air": 5, "fire": 2, "earth": 2, "water": 2}, "aspect_intensity": 22, "chart_complexity": "very_complex"}	{}	{}
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: astra_user
--

COPY public.users (telegram_id, birth_date, birth_time, birth_city, profession, job_position, current_city, gender, request_count, created_at, updated_at, user_segment, activity_level, data_quality_score) FROM stdin;
5960877187	1973-10-16	11:48:00	калининград	программист	кладовщик	калининград	male	27	2025-11-21 13:25:23.116195	2025-11-25 12:06:23.830377	active	medium	90
\.


--
-- Name: biorhythms biorhythms_pkey; Type: CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.biorhythms
    ADD CONSTRAINT biorhythms_pkey PRIMARY KEY (telegram_id, calculation_date);


--
-- Name: calculation_cache calculation_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.calculation_cache
    ADD CONSTRAINT calculation_cache_pkey PRIMARY KEY (telegram_id, target_date, data_type);


--
-- Name: daily_calculations daily_calculations_pkey; Type: CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.daily_calculations
    ADD CONSTRAINT daily_calculations_pkey PRIMARY KEY (telegram_id, target_date);


--
-- Name: ml_models ml_models_pkey; Type: CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.ml_models
    ADD CONSTRAINT ml_models_pkey PRIMARY KEY (model_id);


--
-- Name: user_astro_profile user_astro_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.user_astro_profile
    ADD CONSTRAINT user_astro_profile_pkey PRIMARY KEY (telegram_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (telegram_id);


--
-- Name: idx_astro_profile_ml; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_astro_profile_ml ON public.user_astro_profile USING gin (ml_features);


--
-- Name: idx_astro_profile_telegram_id; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_astro_profile_telegram_id ON public.user_astro_profile USING btree (telegram_id);


--
-- Name: idx_biorhythms_calculation_date; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_biorhythms_calculation_date ON public.biorhythms USING btree (calculation_date);


--
-- Name: idx_biorhythms_composite; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_biorhythms_composite ON public.biorhythms USING btree (telegram_id, calculation_date);


--
-- Name: idx_biorhythms_telegram_id; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_biorhythms_telegram_id ON public.biorhythms USING btree (telegram_id);


--
-- Name: idx_cache_expires; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_cache_expires ON public.calculation_cache USING btree (expires_at);


--
-- Name: idx_cache_telegram_date; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_cache_telegram_date ON public.calculation_cache USING btree (telegram_id, target_date);


--
-- Name: idx_cache_type; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_cache_type ON public.calculation_cache USING btree (data_type);


--
-- Name: idx_daily_calc_has_ml; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_has_ml ON public.daily_calculations USING gin (ml_features);


--
-- Name: idx_daily_calc_hash; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_hash ON public.daily_calculations USING btree (data_hash);


--
-- Name: idx_daily_calc_insights; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_insights ON public.daily_calculations USING gin (basic_insights);


--
-- Name: idx_daily_calc_ml_features; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_ml_features ON public.daily_calculations USING gin (ml_features);


--
-- Name: idx_daily_calc_ml_quality; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_ml_quality ON public.daily_calculations USING btree (ml_data_quality);


--
-- Name: idx_daily_calc_target_date; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_target_date ON public.daily_calculations USING btree (target_date);


--
-- Name: idx_daily_calc_telegram_date; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_telegram_date ON public.daily_calculations USING btree (telegram_id, target_date);


--
-- Name: idx_daily_calc_timestamp; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_timestamp ON public.daily_calculations USING btree (calculation_timestamp);


--
-- Name: idx_daily_calc_trends; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_daily_calc_trends ON public.daily_calculations USING gin (trend_data);


--
-- Name: idx_ml_models_active; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_ml_models_active ON public.ml_models USING btree (is_active);


--
-- Name: idx_ml_models_type; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_ml_models_type ON public.ml_models USING btree (model_type);


--
-- Name: idx_users_activity; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_users_activity ON public.users USING btree (activity_level);


--
-- Name: idx_users_birth_date; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_users_birth_date ON public.users USING btree (birth_date);


--
-- Name: idx_users_data_quality; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_users_data_quality ON public.users USING btree (data_quality_score);


--
-- Name: idx_users_gender; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_users_gender ON public.users USING btree (gender);


--
-- Name: idx_users_profession; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_users_profession ON public.users USING btree (profession);


--
-- Name: idx_users_telegram_id; Type: INDEX; Schema: public; Owner: astra_user
--

CREATE INDEX idx_users_telegram_id ON public.users USING btree (telegram_id);


--
-- Name: biorhythms biorhythms_telegram_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.biorhythms
    ADD CONSTRAINT biorhythms_telegram_id_fkey FOREIGN KEY (telegram_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;


--
-- Name: calculation_cache calculation_cache_telegram_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.calculation_cache
    ADD CONSTRAINT calculation_cache_telegram_id_fkey FOREIGN KEY (telegram_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;


--
-- Name: daily_calculations daily_calculations_telegram_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.daily_calculations
    ADD CONSTRAINT daily_calculations_telegram_id_fkey FOREIGN KEY (telegram_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;


--
-- Name: user_astro_profile user_astro_profile_telegram_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: astra_user
--

ALTER TABLE ONLY public.user_astro_profile
    ADD CONSTRAINT user_astro_profile_telegram_id_fkey FOREIGN KEY (telegram_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 2Pd6cuq6PwHwMoO1YNKWccBRDyitQ6cksF04KDgn0uCbOTzT3bo1VrhjpIfDLUx

