(define (problem bw_hard_015)
  (:domain blocks-world)

  (:objects
    a b c d e f - block
  )

  (:init
    (on_table b)
    (on_table d)
    (on_table e)
    (on_table f)
    (on c b)
    (on a d)
    (clear c)
    (clear a)
    (clear e)
    (clear f)
    (handempty)
  )

  (:goal
    (and
      (on e c)
      (on f e)
      (on a b)
    )
  )
)
