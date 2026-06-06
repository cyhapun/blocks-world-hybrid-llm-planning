(define (problem bw_medium_014)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table d)
    (on_table c)
    (on a d)
    (on b a)
    (clear b)
    (clear c)
    (handempty)
  )

  (:goal
    (on c b)
  )
)
