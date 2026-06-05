(define (domain blocks-world)
  (:requirements :strips :typing)

  (:types block)

  (:predicates
    (on ?x - block ?y - block)
    (on_table ?x - block)
    (clear ?x - block)
    (holding ?x - block)
    (handempty)
  )

  (:action pick-up
    :parameters (?x - block)
    :precondition (and
      (clear ?x)
      (on_table ?x)
      (handempty)
    )
    :effect (and
      (holding ?x)
      (not (clear ?x))
      (not (on_table ?x))
      (not (handempty))
    )
  )

  (:action put-down
    :parameters (?x - block)
    :precondition (and
      (holding ?x)
    )
    :effect (and
      (on_table ?x)
      (clear ?x)
      (handempty)
      (not (holding ?x))
    )
  )

  (:action stack
    :parameters (?x - block ?y - block)
    :precondition (and
      (holding ?x)
      (clear ?y)
    )
    :effect (and
      (on ?x ?y)
      (clear ?x)
      (handempty)
      (not (holding ?x))
      (not (clear ?y))
    )
  )

  (:action unstack
    :parameters (?x - block ?y - block)
    :precondition (and
      (on ?x ?y)
      (clear ?x)
      (handempty)
    )
    :effect (and
      (holding ?x)
      (clear ?y)
      (not (on ?x ?y))
      (not (clear ?x))
      (not (handempty))
    )
  )
)