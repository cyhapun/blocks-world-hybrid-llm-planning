(define (problem bw_hard_001)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (on_table d)
    (on_table e)
    (clear a)
    (clear b)
    (clear c)
    (clear d)
    (clear e)
    (handempty)
  )

  (:goal
    (and
      (on b c)
      (on c d)
    )
  )
)
