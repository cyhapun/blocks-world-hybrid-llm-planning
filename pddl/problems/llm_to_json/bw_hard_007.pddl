(define (problem bw_hard_007)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table b)
    (on_table c)
    (on_table d)
    (on a b)
    (on e d)
    (clear a)
    (clear c)
    (clear e)
    (handempty)
  )

  (:goal
    (and
      (on c a)
      (on e c)
    )
  )
)
