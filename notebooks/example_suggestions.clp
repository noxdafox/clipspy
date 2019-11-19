; This file contains an example of exploratory suggestion of intents.
; It is based on these keys ideas:
;    - Try to explore all intents
;    - Do not suggest the same intent too often
;    - 



;---------------------------------------------------------------------------------
; Global definitions

;
; Global variables
;

; This is the minimum time between two suggestions of the same intent, in seconds.
; 10 minutes
(defglobal ?*MIN_SUGGESTION_TIME* = (* 10 60))

; These are the IDs of some of the current intents in the TV domain.
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

; This is a multifield global variable containing the IDs of the tv domain intents.
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

; This function gets the last element of a multifield value.
(deffunction get_last_element ($?list)
    (nth$ (length$ $?list) $?list)
)

;(deffunction is_last_element (?value $?list)
;    (eq ?value (get_last_element $?list))
;)



;-------------------------------------------------------------------------------
; Deftemplates


; User information
(deftemplate user_info
    (slot id (type STRING))
    (slot type (type INTEGER))
    (slot cluster_id (type INTEGER))
    (slot channel_id (type STRING))
    (slot at_home (type SYMBOL))  ; TRUE | FALSE
    (slot stb (type SYMBOL))  ; TRUE | FALSE
)

; Information reggarding suggestions already made to one given user.
(deftemplate suggested_intent
    (slot user_id (type STRING))
    (slot id (type INTEGER))
    (slot name (type STRING))
    (slot num_requested_day (type INTEGER) (default 0))
    (slot num_requested_week (type INTEGER) (default 0))
    (slot num_suggested_day (type INTEGER) (default 0))
    (slot num_suggested_week (type INTEGER) (default 0))
    (slot num_selected_day (type INTEGER) (default 0))
    (slot num_selected_week (type INTEGER) (default 0))
    (slot last_suggested (type INTEGER) )
)

; Information on the current instant
(deftemplate current_instant
    (slot time_segment (type INTEGER))
    (slot day_of_week (type INTEGER))
)

; Current user session information
(deftemplate current_session
    (slot user_id (type STRING))
    (multislot intents (type INTEGER))
)


;-----------------------------------------------------------------------------
; Deffacts

;(deffacts init_facts
;    (start_reasoning)
;)



;-----------------------------------------------------------------------------
; Rules

;--------------------------------------------
; Add a punctuation to possible suggestions.
; Punctuations are additive for every intent.

(defrule r_explore_1 "Do not suggest intents that have been just suggested"
    (now ?now)
    (suggested_intent (id ?id) (last_suggested ?last_suggested))
    (test (< (- ?now ?last_suggested) ?*MIN_SUGGESTION_TIME*))
    =>
    (assert (intent_suggestion ?id -1000 (gensym)))
)

(defrule r_explore_2 "Explore on TV domain per day"
    (suggested_intent (id ?id) (num_suggested_day ?num_suggested))
    (test (in ?id ?*TV_DOMAIN_INTENTS*))
    (test (< ?num_suggested ?*MAX_SUGGESTIONS_DAY_TV*))
    =>
    (assert (intent_suggestion ?id 0.1 (gensym)))
)

(defrule r_explore_3 "Explore on TV domain per week"
    (suggested_intent (id ?id) (num_suggested_week ?num_suggested))
    (test (in ?id ?*TV_DOMAIN_INTENTS*))
    (test (< ?num_suggested ?*MAX_SUGGESTIONS_WEEK_TV*))
    =>
    (assert (intent_suggestion ?id 0.2 (gensym)))
)

(defrule r_explore_4 "If tv.display is latest intent, suggest tv.search_similar, tv.record"
    (current_session (user_id ?user_id) (intents $?intents))
    (test (eq (get_last_element $?intents) ?*TV_DISPLAY*))
    =>
    (assert (intent_suggestion ?*TV_SEARCH_SIMILAR* 0.5 (gensym)))
    (assert (intent_suggestion ?*TV_RECORD* 0.3 (gensym)))
)

(defrule r_explore_5 "If tv.search in current session, suggest tv.question_time_loc"
    (current_session (user_id ?user_id) (intents $?intents))
    (test (in ?*TV_SEARCH* $?intents))
    =>
    (assert (intent_suggestion ?*TV_QUESTION_TIME_LOC* 0.5 (gensym)))
)


;-----------------------------------
; Auxiliary rules

(defrule r_test_get_time "This rules is used to get the current time"
    (not (now ?))
    =>
    (printout t "Unix time " (get_time) crlf)
    (assert (now (get_time)))
)

