(define (problem bw_medium_009)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table d)
    (on c d)
    (on b a)
    (clear c)
    (clear b)
    (handempty)
  )

  (:goal
    (on b c)
  )
)
