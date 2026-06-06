(define (problem bw_hard_002)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table a)
    (on_table c)
    (on_table e)
    (on b a)
    (on d c)
    (clear b)
    (clear d)
    (clear e)
    (handempty)
  )

  (:goal
    (and
      (on e b)
      (on d a)
    )
  )
)
