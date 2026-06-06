(define (problem bw_medium_009)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table d)
    (on_table a)
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
