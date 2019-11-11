;
; This module defines data structures and functions used to manage SLOTS.
;
; A SLOT is an unordered fact with two fields:
;    - name: The name of the slot.
;    - value: A single value.
;
; An MSLOT is an unordered fact with two fields:
;    - name: The name of the slot.
;    - value: A multiple value (list or multislot)
;
; SLOT facts are supposed to be unique, i.e. only one fact or a given name should exist at a given time.
; To ensure uniqueness use the functions 'assert_unique_slot' and 'assert_unique_mslot'.
;

(deftemplate SLOT (slot name (type STRING)) (slot value))
(deftemplate MSLOT (slot name (type STRING)) (multislot value))

(deffunction assert_unique_slot (?name ?value)
	; 1. Retract all slots with different values
	(do-for-all-facts ((?f SLOT)) (and (eq ?f:name ?name) (neq ?f:value ?value))
		(retract ?f)
	)
	; 2. Check if the same slot is already asserted. If so, do nothing. Else, assert the fact.
	; This check is inteneded to avoid unecessary reaserting of facts.
	(bind ?rem_facts (find-all-facts ((?f SLOT)) (eq ?f:name ?name)))
	(if (= (length$ ?rem_facts) 0) then
			(assert (SLOT (name ?name) (value ?value)))
	)
)

; This is an alias of assert_unique_slot
(deffunction aus (?name ?value)
    (assert_unique_slot ?name ?value)
)

(deffunction assert_unique_mslot (?name $?value)
	; 1. Retract all slots with different values
	(do-for-all-facts ((?f MSLOT)) (and (eq ?f:name ?name) (neq ?f:value ?value))
		(retract ?f)
	)
	; 2. Check if the same slot is already asserted. If so, do nothing. Else, assert the fact.
	; This check is inteneded to avoid unecessary reaserting of facts.
	(bind ?rem_facts (find-all-facts ((?f MSLOT)) (eq ?f:name ?name)))
	(if (= (length$ ?rem_facts) 0) then
			(assert (MSLOT (name ?name) (value ?value)))
	)
)

; This is an alias of assert_unique_mslot
(deffunction aums (?name $?value)
    (assert_unique_mslot ?name ?value)
)

