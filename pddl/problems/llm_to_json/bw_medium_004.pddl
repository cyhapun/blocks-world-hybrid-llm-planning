(define (problem bw_medium_004)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table d)
    (on b a)
    (on c b)
    (clear c)
    (clear d)
    (handempty)
  )

  (:goal
    (on d c)
  )
)
