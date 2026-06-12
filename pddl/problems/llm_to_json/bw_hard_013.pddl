(define (problem bw_hard_013)
  (:domain blocks-world)

  (:objects
    a b c d e f - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (on d a)
    (on e b)
    (on f c)
    (clear d)
    (clear e)
    (clear f)
    (handempty)
  )

  (:goal
    (and
      (on f d)
      (on e a)
    )
  )
)
