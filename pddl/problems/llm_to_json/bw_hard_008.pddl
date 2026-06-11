(define (problem bw_hard_008)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table c)
    (on_table a)
    (on_table e)
    (on b c)
    (on d a)
    (clear b)
    (clear d)
    (clear e)
    (handempty)
  )

  (:goal
    (and
      (on e d)
      (on b a)
    )
  )
)
