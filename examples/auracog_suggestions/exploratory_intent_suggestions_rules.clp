
; Rules for exploratory suggestions on intents

;-------------------------------------------------
; Information elements to take into account in reasoning:
;
; - Cluster ID
; - Type of user
; - User is at home
; - Channel ID
; - STB is available
; --> (user (id ?) (type ?) (cluster_id ?) (channel_id ?) (at_home ?) (stb ?stb)
;
; - Time of day (time segment)
; - Day of week
; --> (general (time_segment ?) (day_of_week ?))
;
; - Number of times a user requests one intent for a given time period (day, week)
; - Number of times one intent is suggested for a given time period (day, week)
; - Number of times a user select a suggested intent for a given time period (day, week)
; - Time of last suggestion for every intent
; --> (intent (id ?id)
;             (num_requested_day ?) (num_requested_week ?)
;             (num_suggested_day ?) (num_suggested_week ?)
;             (num_selected_day ?) (num_selected_week ?)
;             (last_suggested ?)
;     )
;
; - Intents in current session
; --> (current_session (intents ?multislot_value))
;
;------------------------------------------------

(deftemplate user
    (slot id (type STRING))
    (slot type (type INTEGER))
    (slot cluster_id (type INTEGER))
    (slot channel_id (type STRING))
    (slot at_home (type SYMBOL))
    (slot stb (type SYMBOL))
)

(deftemplate general
    (slot time_segment (type INTEGER))
    (slot day_of_week (type INTEGER))
)

(deftemplate intent
    (slot id (type INTEGER))
    (slot num_requested_day (type INTEGER))
    (slot num_requested_week (type INTEGER))
    (slot num_suggested_day (type INTEGER))
    (slot num_suggested_week (type INTEGER))
    (slot num_selected_day (type INTEGER))
    (slot num_selected_week (type INTEGER))
    (slot last_suggested (type INTEGER))
)

(deftemplate current_session
    (multislot intents (type INTEGER))
)


;------------------------------------------------
; Global definitions

;
; Global variables
;
(defglobal ?*MIN_SUGGESTION_TIME* = (* 10 60))
(defglobal ?*MAX_SUGGESTIONS_DAY_TV* = 2)
(defglobal ?*MAX_SUGGESTIONS_WEEK_TV* = 7)

(defglobal ?*TV_VOD_EPG_INFORMATION* = 171)
(defglobal ?*CAROUSEL_INFO* = 172)
(defglobal ?*TV_DETAILS* = 173)

(defglobal ?*TV_SEARCH* = 191)
(defglobal ?*TV_CONTENT_GET_INFO* = 192)
(defglobal ?*TV_QUESTION_TIME_LOC* = 193)
(defglobal ?*TV_SEARCH_SIMILAR* = 194)

(defglobal ?*TV_DISPLAY* = 195)
(defglobal ?*TV_LAUNCH* = 196)

(defglobal ?*TV_CHANNEL_DOWN* = 211)
(defglobal ?*TV_CHANNEL_UP* = 212)
(defglobal ?*FROM_BEGINNING* = 221)

(defglobal ?*TV_RECORD* = 222)
(defglobal ?*TV_PAUSE* = 223)
(defglobal ?*TV_RESUME* = 224)

(defglobal ?*TV_VOLUME_DOWN* = 241)
(defglobal ?*TV_VOLUME_UP* = 242)

(defglobal ?*TV_MUTE* = 243)
(defglobal ?*TV_UNMUTE* = 244)

(defglobal ?*TV_LANGUAGE_CHANGE* = 245)
(defglobal ?*TV_SUBTITLES_REMOVE* = 246)


(defglobal ?*TV_DOMAIN_INTENTS* = (create$ ?*TV_VOD_EPG_INFORMATION* ?*CAROUSEL_INFO* ?*TV_DETAILS* ?*TV_SEARCH*
                                           ?*TV_CONTENT_GET_INFO* ?*TV_QUESTION_TIME_LOC* ?*TV_SEARCH_SIMILAR*
                                           ?*TV_DISPLAY* ?*TV_LAUNCH* ?*TV_CHANNEL_DOWN* ?*TV_CHANNEL_UP*
                                           ?*FROM_BEGINNING* ?*TV_RECORD* ?*TV_PAUSE* ?*TV_RESUME* ?*TV_VOLUME_DOWN*
                                           ?*TV_VOLUME_UP* ?*TV_MUTE* ?*TV_UNMUTE* ?*TV_LANGUAGE_CHANGE*
                                           ?*TV_SUBTITLES_REMOVE*))

; This function checks whether one element is contained in a multislot value.
(deffunction in (?value $?list)
    (bind ?res (member$ ?value $?list))
    (return (eq (type ?res) INTEGER))
)


;------------------------------------------------
; Rules
;


(defrule r_explore_1 "Do not suggest intents that have been just suggested"
    (intent (id ?id) (last_suggested ?last_suggested))
    (test (< ?last_suggested ?*MIN_SUGGESTION_TIME*))
    =>
    (assert (intent_suggestion ?id -1000))
)

(defrule r_explore_2 "Explore on TV domain per day"
    (intent (id ?id) (num_suggested_day ?num_suggested))
    (test (in ?id ?*TV_DOMAIN_INTENTS*))
    (test (< ?num_suggested ?*MAX_SUGGESTIONS_DAY_TV*))
    =>
    (assert (intent_suggestion ?id 0.1))
)

(defrule r_explore_3 "Explore on TV domain per week"
    (intent (id ?id) (num_suggested_week ?num_suggested))
    (test (in ?id ?*TV_DOMAIN_INTENTS*))
    (test (< ?num_suggested ?*MAX_SUGGESTIONS_WEEK_TV*))
    =>
    (assert (intent_suggestion ?id 0.1))
)



