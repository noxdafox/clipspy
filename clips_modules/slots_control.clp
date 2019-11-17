;
; This module defines functions to uniquely assert slot type facts.
;

(deffunction count-facts (?template)
	(bind ?count 0)
	(do-for-all-facts ((?fct ?template)) TRUE
		(bind ?count (+ ?count 1)))
    ?count
)

; This assertion is needed to force the implicit definition of the deftemplate 'slot', which is used in the
; count-slots and assert_unique_slot functions.
(deffacts initial_slot
    (slot __initial_slot__)
)

(deffunction count-slots (?name)
	(bind ?count 0)
	(do-for-all-facts ((?fct slot)) (eq (nth$ 1 ?fct:implied) ?name)
		(bind ?count (+ ?count 1)))
    ?count
)

(deffunction assert_unique_slot (?name ?value)
	; 1. Retract all slots with different values
	(do-for-all-facts ((?f slot)) (and (eq (nth$ 1 ?f:implied) ?name) (neq (rest$ ?f:implied) (create$ ?value)))
		(retract ?f)
	)
	; 2. Check if the same slot is already asserted. If so, do nothing; else, assert the fact.
	; This check is intended to avoid unnecessary reasserting of facts.
	(bind ?rem_facts (find-all-facts ((?f slot)) (eq (nth$ 1 ?f:implied) ?name)))
	(if (= (length$ ?rem_facts) 0) then
			(assert (slot (create$ ?name ?value)))
	)
)

; This is an alias of assert_unique_slot
(deffunction aus (?name ?value)
    (assert_unique_slot ?name ?value)
)

; Retract the (slot __initial_slot) fact since it is not longer needed.
(defrule retract_initial_slot "This rule retracts the __initial_slot__ rule, needed for managing unique slots"
    ?f <- (slot __initial__slot__)
    =>
    (retract ?f)
)
