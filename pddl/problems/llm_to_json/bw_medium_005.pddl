(define (problem bw_medium_005)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on c b)
    (clear c)
    (clear d)
    (handempty)
  )

  (:goal
    (on a d)
  )
)
