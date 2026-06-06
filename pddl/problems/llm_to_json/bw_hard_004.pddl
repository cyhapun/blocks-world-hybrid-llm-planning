(define (problem bw_hard_004)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table d)
    (on_table b)
    (on_table e)
    (on a d)
    (on c b)
    (clear a)
    (clear c)
    (clear e)
    (handempty)
  )

  (:goal
    (and
      (on e a)
      (on c d)
    )
  )
)
