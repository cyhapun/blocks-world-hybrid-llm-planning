(define (problem bw_hard_005)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table a)
    (on_table d)
    (on b a)
    (on c b)
    (on e d)
    (clear c)
    (clear e)
    (handempty)
  )

  (:goal
    (and
      (on e c)
      (on_table b)
    )
  )
)
